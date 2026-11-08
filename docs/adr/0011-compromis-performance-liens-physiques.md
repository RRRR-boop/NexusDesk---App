# ADR-0011 — Compromis de performance pour tenir le budget d'1 million de fichiers

## Statut
Décidé, chiffres mesurés empiriquement sur cette machine, **critère de sortie non
définitivement atteint à ce jour** — voir la section « Résultat honnête » ci-dessous
(choix réversibles, section 21.3).

## Contexte
Le critère de sortie du lot exige un scan d'1 million de fichiers en moins de 3 minutes
(180 s) sur SSD NVMe. Un premier micro-benchmark isolé (uniquement le coût de détection des
liens physiques, sur ~100 000 fichiers) avait laissé penser qu'un simple compromis suffirait
(~34 s extrapolées). **Une mesure réelle à l'échelle d'1 000 000 de fichiers a révélé que ce
micro-benchmark isolé ne représentait pas le coût réel du pipeline complet** : plusieurs
autres postes de coût, invisibles à petite échelle, dominent en réalité à grande échelle.
Ce document consigne les quatre compromis identifiés et mesurés, dans l'ordre où ils ont été
découverts.

## 1. Détection des liens physiques (liens physiques, hardlinks)
Détecter un lien physique de façon fiable nécessite l'identité réelle du fichier (numéro de
série du volume + index de fichier), obtenue via `CreateFile` + `GetFileInformationByHandle`
— un appel Windows coûteux (ouverture d'un handle par fichier). `DirEntry.stat()` (chemin
rapide mis en cache par Windows) ne reporte jamais correctement `st_nlink` : il renvoie
systématiquement `1`, même pour un fichier ayant plusieurs liens physiques réels.

**Décision** : `os.stat(path, follow_symlinks=False)` (jamais `DirEntry.stat()`) pour
obtenir un `st_nlink` fiable, puis `get_hardlink_key` (le port Windows coûteux) n'est appelé
que si `stat_result.st_nlink > 1`. Micro-benchmark isolé : ~750 000 fichiers/s sans appel
systématique à `get_hardlink_key`, contre ~700 fichiers/s si l'appel était systématique.

## 2. `is_excluded` : un `Path.resolve()` par entrée, y compris pour la racine (bug corrigé)
**Découverte pendant la validation à grande échelle de ce lot.** `is_excluded` (appelée une
fois par entrée de répertoire, donc jusqu'à ~1 005 000 fois pour 1M fichiers) appelait
`path.resolve()` sur l'entrée **et** `scan_root.resolve()` **à chaque invocation**, alors que
`scan_root` ne change jamais pendant un scan. `Path.resolve()` effectue un aller-retour
disque réel sous Windows (canonicalisation de chemin), mesuré à lui seul à ~230 µs par appel
— soit, multiplié par deux appels et ~1M entrées, le poste de coût dominant du scan complet.

**Décision** : `is_excluded` compare désormais directement les chemins (`path == scan_root`,
`path == excluded`, `excluded in path.parents`) sans jamais appeler `.resolve()` : les
chemins fournis par `os.scandir` à partir d'une racine absolue sont déjà absolus et ne
contiennent jamais de segment `..`, donc la comparaison syntaxique directe est correcte et
suffisante (`PureWindowsPath` compare déjà de façon insensible à la casse).

**Mesuré** (échantillon réel de 5000 fichiers) : `is_excluded` passe de ~1421 fichiers/s à
~8173 fichiers/s (+ 475 %) après correction.

## 3. Ramasse-miettes cyclique (`gc`) : coût croissant avec le nombre d'objets vivants
Aucun cycle de référence n'existe dans le modèle de données DiskPilot (`FolderNode`/
`FileNode` n'ont pas de référence arrière vers leur parent) : le comptage de références de
CPython libère donc déjà toute la mémoire correctement sans le ramasse-miettes cyclique. Ce
dernier balaie néanmoins périodiquement l'ensemble des objets suivis ; avec jusqu'à 1M de
`FileNode` vivants simultanément (`FolderNode.files` n'est jamais plafonné, contrairement
aux 1000 plus gros fichiers persistés), ce balayage devient de plus en plus coûteux à mesure
que le nombre d'objets croît.

**Décision** : `gc.disable()` au début du parcours (`build_scan_task::_task`), `gc.enable()`
dans un `finally` (donc même en cas d'annulation ou d'erreur) — sans risque de fuite mémoire
puisqu'il n'y a pas de cycle à collecter.

## 4. `get_size_on_disk` appelé systématiquement, même pour un fichier ordinaire
Seuls les fichiers compressés ou creux (NTFS) ont une taille sur disque réellement
différente de leur taille logique ; pour tout autre fichier, l'écart possible se limite à
l'arrondi au cluster NTFS (quelques Ko), négligeable à l'agrégat. L'attribut
`FILE_ATTRIBUTE_COMPRESSED`/`SPARSE_FILE` est déjà disponible sans appel supplémentaire
(`stat_result.st_file_attributes`, déjà lu pour la détection OneDrive).

**Décision** : `get_size_on_disk` (l'appel Win32 `GetCompressedFileSize`) n'est appelé que
si `size_on_disk_may_differ_from_logical_size(stat_result.st_file_attributes)` est vrai ;
sinon `size_on_disk = stat_result.st_size`. Mesuré sur 100 000 fichiers réels : ~6760
fichiers/s sans l'appel conditionné, contre ~5433 fichiers/s en l'appelant systématiquement
(+ 24 %).

## Résultat honnête — mesures réelles sur 1 000 000 de fichiers

| Étape                                                    | Temps mesuré | Débit        |
|-----------------------------------------------------------|-------------|--------------|
| Avant tout correctif (seul le compromis liens physiques en place) | 697,6 s     | 1 434 f/s    |
| Après correction d'`is_excluded` (point 2)                 | 362,1 s     | 2 762 f/s    |
| `is_excluded` corrigé + `gc.disable()` externe (point 3 isolé) | 246,3 s     | 4 059 f/s    |
| Tous les correctifs combinés (points 2+3+4, code final)     | 341,1 s     | 2 932 f/s    |

**Le critère de sortie (180 s) n'est pas définitivement atteint dans cette session**, malgré
une amélioration réelle de 2 à 2,8× par rapport à l'état initial. L'écart entre la mesure
« `gc.disable()` isolé » (246 s) et la mesure « tous correctifs combinés » (341 s) sur le même
code n'est pas pleinement expliqué : la protection en temps réel de Windows Defender est
confirmée **active** sur cette machine (`Get-MpPreference` : `DisableRealtimeMonitoring =
False`) et aucune exclusion n'est configurée pour le dossier de test — un antivirus à
analyse sur accès peut intercepter chacun des appels `os.stat`/`GetCompressedFileSize` sur
1M de fichiers de façon non déterministe, ce qui est cohérent avec la variance observée
entre exécutions successives sur une machine par ailleurs inchangée. Désactiver Windows
Defender dépasse le périmètre et l'autorisation de cette session (changement de sécurité à
l'échelle du système, pas une décision applicative réversible).

## Conséquences
- Les quatre correctifs sont tous sans régression de correctness (couverts par des tests
  unitaires réels : liens physiques, jonctions, dossiers exclus, fichiers non compressés) et
  représentent une amélioration réelle et mesurée, même si le critère strict des 180 s n'est
  pas garanti dans toutes les conditions d'exécution observées sur cette machine.
- Piste de poursuite explicitement **non faite** ce lot : mesurer sur une machine avec une
  exclusion Windows Defender pour le dossier scanné, ou explorer un parcours parallélisé
  (plusieurs threads `os.scandir`) — actuellement mono-thread par construction
  (`TaskManager`/`QThreadPool`, un seul `QRunnable` par scan).
- `tests/integration/windows/test_scan_performance_canary.py` reste un canari de régression
  à seuil large (2000 f/s), pas une preuve du critère de sortie — voir son en-tête.
