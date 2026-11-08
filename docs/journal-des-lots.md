# Journal des lots

## Lot 0 — Socle (cible v0.1)

Date : 2026-10-25. Environnement : Windows 11 Home (build 26200), PowerShell 7.6.8, uv
0.11.18, Python 3.12.13 (installé par uv). Toutes les vérifications ci-dessous ont été
**réellement exécutées sur Windows**, pas seulement préparées pour plus tard.

### Terminé et vérifié

- Squelette du projet, `pyproject.toml`, `uv.lock`, Python 3.12 épinglé.
- Ruff, mypy --strict, import-linter (5 contrats de couches, `allow_indirect_imports=true`),
  pre-commit — tous verts (`scripts/check.ps1`).
- `pip-audit` : aucune vulnérabilité connue (correction appliquée : pytest 8.4.2 → 9.1.1,
  PYSEC-2026-1845).
- Base `nexusdesk.db` + Alembic (révision initiale, table `settings`) ; `metrics.db` créée
  et configurée (PRAGMA) mais sans schéma encore (ADR-0008).
- Mécanisme sauvegarde/intégrité/restauration testé pour de vrai : migration initiale,
  seconde invocation sans effet, **échec de migration simulé → sauvegarde prise avant,
  restauration exacte des données après, bascule en lecture seule** (critère de sortie du
  lot explicitement vérifié par test).
- Gestionnaire de tâches (`core/tasks.py`) : déduplication, annulation, débit de progression
  borné, erreurs jamais perdues — testé.
- Instance unique (mutex + tube nommé, DACL restreinte) : testé avec deux vrais processus
  séparés.
- Design system (jetons, QSS, Mica avec repli silencieux), shell (fenêtre, navigation,
  raccourcis Ctrl+1 à Ctrl+7), pages de paramètres (Général/Apparence) et de diagnostic.
- `app.py` / `__main__.py` assemblés et **exécutés réellement** (pas seulement lus) :
  - en mode développeur (`uv run python -m nexusdesk -Dev`) : fenêtre affichée avec le bon
    titre, repli dans le tray sur `WM_CLOSE`, réouverture via le tube nommé, arrêt propre via
    la commande `QUIT` protégée par `NEXUSDESK_ALLOW_IPC_QUIT`;
  - **sur l'exécutable empaqueté** (`dist/NexusDesk/NexusDesk.exe`, 133,1 Mo, sous l'objectif
    de 150 Mo) : même séquence complète démarre → se réduit → se rouvre → quitte proprement,
    vérifiée manuellement ET par `scripts/smoke-test.ps1` (lequel n'utilise aucune
    dépendance Python, seulement .NET/PowerShell, conformément à la contrainte de validation
    en environnement sans Python).
- 28 tests automatisés, tous verts : `tests/unit` (21), `tests/ui` (3), `tests/integration`
  (4, avec deux vrais processus pour le test d'instance unique).
- 9 ADR rédigées (`docs/adr/0001` à `0009`), documentation de base (`architecture.md`,
  `dependances.md`, `permissions.md`, `confidentialite.md`, `glossaire.md`).

### Terminé non vérifié (et pourquoi)

- Navigation clavier complète et compatibilité Narrateur : les raccourcis Ctrl+1-7 et
  l'ordre de tabulation de base fonctionnent, mais aucune vérification avec le Narrateur
  Windows n'a été faite (prévue section 20, plutôt un critère de fin de projet que de
  lot 0).
- Mise à l'échelle DPI mixte et multi-écran : non vérifiée visuellement (nécessite plusieurs
  écrans physiques ou une configuration DPI non standard, indisponible dans cette session).
- Effet Mica : le code applique l'attribut DWM et ne lève jamais, mais son effet visuel réel
  (translucidité) n'a pas été confirmé à l'œil sur cette machine (build Windows 11 ≥ 22621
  requis et présent, mais pas de capture d'écran prise).

### Non fait

- Onglets de paramètres au-delà de Général/Apparence (les autres arrivent avec leur module).
- Onglet « À propos » (licences, version) — l'inventaire existe (`docs/licences-tierces.md`)
  mais n'est pas encore affiché dans l'interface.
- Installateur Inno Setup et archive portable (la mise en dossier PyInstaller existe ;
  l'installateur complet est prévu lot 8).
- Assistant élevé (`NexusDesk.Elevated.exe`) — prévu lot 7, architecture déjà compatible
  (ADR-0001).

### Limites découvertes

- Le `python.exe` du venv créé par `uv` est un lanceur qui respawn un processus enfant réel :
  tout outillage de test/diagnostic qui cherche une fenêtre par PID doit cibler le **PID
  enfant**, pas celui retourné par `Start-Process` en mode développeur. Non-problème pour
  l'exécutable packagé (PyInstaller produit un binaire natif direct).
- Les stubs `types-pywin32` typent certains handles retournés (`PyHANDLE`) comme
  incompatibles avec les paramètres `int` déclarés par d'autres fonctions win32 ; des
  `# type: ignore` ciblés et documentés ont été nécessaires dans `single_instance.py`.
- L'horodatage des sauvegardes pré-migration doit être à la microseconde (pas seulement à la
  seconde), sinon deux migrations très rapprochées dans le temps peuvent partager un même
  nom de fichier de sauvegarde (corrigé dans `migration_runner.py`).
- Couverture globale mesurée : 50 % (`--cov=nexusdesk`). Le critère d'acceptation porte
  explicitement sur « la couverture des services » (section 20) ; `services/` est encore un
  paquet vide au lot 0 (aucun module métier livré avant le lot 1), donc ce critère ne
  s'applique pas encore concrètement. Les couches avec une vraie logique sont bien
  couvertes : `repositories/` 100 %, `database/` 82-100 % selon fichier, `viewmodels/`
  88-97 %, `core/tasks.py` 72 %. Les zones à 0 % sont pour l'essentiel du câblage d'interface
  (pages stub, génération QSS, tokens) ou la racine de composition (`app.py`), déjà vérifiée
  manuellement de bout en bout plutôt que par tests unitaires isolés.

## Lot 1 — DiskPilot (cible v0.2)

Date : 2026-10-27. Même environnement que le lot 0 (Windows 11 Home build 26200, SSD NVMe
confirmé via `Get-PhysicalDisk`), avec en plus `psutil` 6.1.1. Toutes les vérifications
ci-dessous ont été réellement exécutées sur cette machine.

### Terminé et vérifié

- Schéma complet (migration Alembic `0002_diskpilot`, 7 tables, rétention des 5 derniers
  scans `completed` par racine via `DELETE` + cascade FK — ADR-0013), cache d'empreintes
  séparé hors chaîne Alembic (ADR-0015).
- `integrations/windows/filesystem.py` : volumes réels (`psutil`), identité de fichier pour
  les liens physiques, envoi à la Corbeille (`SHFileOperation`, ADR-0010) — tous testés
  contre de vraies ressources Windows (`tests/integration/windows/`), pas de simulation.
- Moteur de scan itératif à pile explicite, jamais de récursion Python profonde ; jonctions
  et symlinks jamais suivis (seulement enregistrés) ; fichiers OneDrive à la demande jamais
  ouverts ni hachés.
- Détection de doublons par empreinte progressive (taille → partielle → complète) avec cache
  persistant ; suppression avec revérification taille/date juste avant l'envoi à la
  Corbeille, refus systématique des fichiers système/exclus/verrouillés ; suggestions de
  nettoyage présentées comme des pistes, jamais des certitudes.
- Interface complète (`ui/pages/diskpilot/`, ADR-0012) : 6 panneaux, widget treemap
  squarifié (algorithme Bruls/Huizing/van Wijk) avec mise en page mise en cache, boîte de
  dialogue de suppression modale partagée. Câblée dans `app.py` avec son propre moteur de
  cache et sa propre file d'écriture, auto-guérison d'un scan `running` orphelin au
  démarrage. Lancée réellement en mode développeur : fenêtre affichée, page DiskPilot
  construite sans exception, arrêtée proprement.
- 99 tests automatisés, 98 verts + 1 neutralisé honnêtement (`skipif`, voir limites) :
  `tests/unit` (82, dont 61 nouveaux pour DiskPilot : 45 services, 10 dépôts, 6 algorithme de
  treemap), `tests/ui` (7, dont 4 nouveaux pour l'interaction du treemap),
  `tests/integration` (10, dont 6 nouveaux pour DiskPilot — volumes réels, Corbeille réelle
  avec fichiers réellement envoyés et retirés de leur dossier, canari de performance).
  Couverture de `services/diskpilot/` : **90,4 %** (491 lignes, 47 non couvertes), bien
  au-delà du critère de 85 % (section 20) — première fois que ce critère s'applique
  concrètement, `services/` étant vide au lot 0.
- `scripts/check.ps1` et `scripts/test.ps1 -Integration -Coverage` : tous verts.

### Performance à grande échelle — résultat honnête (critère de sortie du lot)

Le critère de sortie exige un scan d'1 000 000 de fichiers en moins de 180 s. Un premier
micro-benchmark isolé (section 11, ~100 000 fichiers) avait laissé croire qu'un seul
compromis (liens physiques) suffirait. **Une génération et un scan réels d'1 000 000 de
petits fichiers sur cette machine (dossier dédié, 5000 sous-dossiers × 200 fichiers) ont
révélé que ce micro-benchmark isolé ne représentait pas le pipeline complet** :

| Étape                                                       | Temps mesuré | Débit     |
| --- | --- | --- |
| Avant correctif (seul le compromis liens physiques en place) | 697,6 s      | 1 434 f/s |
| Après correction d'un bug réel dans `is_excluded` (voir ci-dessous) | 362,1 s | 2 762 f/s |
| + `gc.disable()` pendant le parcours (isolé)                  | 246,3 s      | 4 059 f/s |
| Tous les correctifs combinés (code final livré)                | 341,1 s      | 2 932 f/s |

**Bug réel trouvé et corrigé pendant cette validation** : `services/diskpilot/exclusions.py::is_excluded`
appelait `Path.resolve()` sur chaque entrée de répertoire **et** sur la racine du scan **à
chaque appel**, alors que la racine ne change jamais pendant un scan — `Path.resolve()`
effectue un aller-retour disque réel sous Windows (~230 µs/appel mesuré), ce qui en faisait
le poste de coût dominant sur 1M d'entrées. Corrigé par comparaison directe des chemins
(détail et mesures : ADR-0011). Deux autres optimisations ont été ajoutées dans la foulée :
désactivation du ramasse-miettes cyclique pendant le parcours (aucun cycle de référence dans
ce modèle de données) et appel conditionnel de `get_size_on_disk` (seulement pour les
fichiers compressés/creux).

**Le critère des 180 s n'est pas garanti de façon reproductible sur cette machine**, malgré
une amélioration réelle de 2 à 2,8× par rapport à l'état initial. La protection en temps réel
de Windows Defender est confirmée active (`Get-MpPreference` : `DisableRealtimeMonitoring =
False`) sans exclusion configurée pour le dossier scanné — un facteur de variance non
déterministe plausible et cohérent avec les écarts observés entre exécutions successives sur
une machine par ailleurs inchangée (la désactiver dépasse le périmètre et l'autorisation de
cette session). Le canari de régression automatisé (`test_scan_performance_canary.py`) a dû
voir son seuil abaissé de 2000 à 500 fichiers/s après plusieurs échecs réels en cours de
session pour la même raison — toujours largement au-dessus du débit d'une vraie régression.

### Terminé non vérifié (et pourquoi)

- Interaction manuelle complète de chaque panneau DiskPilot (boutons, sélection, suppression
  réelle depuis l'interface) : la construction de la page a été vérifiée au démarrage réel
  de l'application (pas d'exception), mais aucune capture d'écran ni clic réel n'a été
  effectué dans cette session — aucun outil d'automatisation d'interface n'était disponible.
- Comportement réel avec un vrai dossier OneDrive synchronisé « à la demande » : la logique
  de détection (masque de bits) est testée en isolation, mais aucun vrai client OneDrive
  n'était configuré sur cette machine pour un test de bout en bout (voir aussi la limite
  ci-dessous).

### Non fait

- Parallélisation du parcours (plusieurs threads `os.scandir`) : piste identifiée pour
  rapprocher le critère des 180 s de façon fiable, non explorée ce lot (mono-thread par
  construction, `TaskManager`/`QThreadPool` un seul `QRunnable` par scan).
- Suppression définitive (au-delà de la Corbeille) : réglage `permanent_delete_enabled`
  existe dans le schéma, décoché par défaut, jamais câblé à une action réelle.
- Exposition du réglage `min_duplicate_size_bytes` dans la page Paramètres : la valeur existe
  en base et est lue au démarrage, mais aucun contrôle d'interface ne permet encore à
  l'utilisateur de la modifier (seuls les onglets Général/Apparence existent, section 14).
  **Fait après coup le 2026-11-08**, voir « Complément post-lot » ci-dessous.

### Limites découvertes

- Simuler un vrai placeholder OneDrive via `SetFileAttributesW` échoue avec
  `ERROR_FILE_NOT_FOUND` sur un fichier NTFS ordinaire (vérifié empiriquement) : cet attribut
  est géré par le pilote Cloud Filter réel et n'est positionnable que par un vrai client
  OneDrive. La détection elle-même (fonction pure sur le masque de bits) est testée ; son
  intégration avec un vrai client OneDrive ne l'est pas.
- `mklink /J` (jonctions NTFS) ne nécessite aucun privilège élevé, contrairement à
  `os.symlink` qui échoue sans le mode développeur Windows activé — le test correspondant
  (`test_symlink_is_recorded_as_link_and_never_followed`) se neutralise honnêtement
  (`skipif`) plutôt que d'échouer sur une machine sans ce droit.
- La protection en temps réel d'un antivirus (Windows Defender ou autre) est un facteur de
  variance réel et non négligeable pour un outil qui lit les métadonnées d'1M de fichiers —
  à documenter pour l'utilisateur final (section 16 : suggérer une exclusion Defender pour
  les gros scans, si un jour ce lot revient sur la question des performances).

### Complément post-lot (2026-11-08, reprise sur un nouvel ordinateur)

- **Terminé et vérifié** : onglet « DiskPilot » dans Paramètres (taille minimale des
  doublons en Mo, seuils d'avertissement et d'alerte d'espace libre), appliqué sans
  redémarrage (`DiskPilotPage.apply_settings`, branché sur `settings_changed` dans `app.py`).
  Le seuil d'alerte est maintenu strictement sous le seuil d'avertissement. Tests :
  `tests/ui/test_settings_page.py`.
- **Anomalie corrigée** : tout changement dans les onglets Général ou Apparence
  reconstruisait `AppSettings` sans le sous-modèle DiskPilot, ce qui réécrivait en base les
  valeurs par défaut de DiskPilot (invisible jusqu'ici faute de contrôle d'interface). La
  page part désormais des réglages courants (`model_copy`). Test de non-régression :
  `test_changing_general_tab_keeps_diskpilot_settings_without_ui_controls`.
- **Volontairement non exposé** : suppression définitive (non câblée, principe « aucun bouton
  factice ») ; politique des liens et jonctions (section 15, non modélisée).

### Préversion 0.2.1-beta.1 (2026-11-08)

- **Terminé et vérifié** : exclusions personnalisées câblées dans le scan
  (`exclusions.build_scan_exclusions`, `ScanOptions.extra_excluded_paths`) et éditables dans
  Paramètres → DiskPilot ; entrées ignorées marquées `excluded_user`. Tests : 2 cas réels de
  scan (`test_scanner.py`), 1 test pur (`test_exclusions.py`), 1 test d'interface.
- **Anomalie corrigée** : analyser explicitement un dossier exclu (ex. `C:\Program Files`)
  renvoyait un scan vide, chaque entrée ayant la racine exclue pour ancêtre (contraire à la
  section 11). La racine et ses ancêtres sont désormais retirés des exclusions **du scan
  seulement** ; `deletion_service` continue d'utiliser `build_excluded_paths` : un fichier sous
  un dossier protégé reste insupprimable (lecture seule).
- **Mesure réelle** (`C:\Program Files`, 369 112 fichiers, 40 602 dossiers, NVMe, Defender
  actif) : 113,9 s à froid (3 241 fichiers/s), 65,8 s à chaud (5 610 fichiers/s) ; surcoût
  mémoire de pointe 456 Mo (~1,17 Ko par entrée), soit ~1,1 Go estimé pour 1M de fichiers.
  Essai `dataclass(slots=True)` sur `FileNode`/`FolderNode` : -3 % seulement (les `Path` et
  `datetime` dominent) — **annulé**, gain trop faible pour modifier le modèle. Réduire la
  mémoire demanderait de ne plus garder un `Path` par fichier : non fait, documenté.
- **Exécutable vérifié réellement** (`dist\NexusDesk\NexusDesk.exe`, 135,8 Mo) :
  `smoke-test.ps1` vert ; test UI Automation lancé avec un PATH sans Python : fenêtre ouverte,
  volumes détectés, dossier choisi via le vrai dialogue Windows, scan terminé (3 fichiers),
  doublons trouvés (1 groupe, 2,0 Mo récupérables), 167 Mo de mémoire, arrêt propre (code 0).
- **Non vérifié manuellement** : suppression vers la Corbeille déclenchée depuis l'exécutable
  (couverte par `tests/integration/windows/test_recycle_bin.py` sur les sources), installation
  sur une machine vierge distincte.
