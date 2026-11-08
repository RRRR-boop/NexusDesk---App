# Architecture (Lots 0-1)

Voir aussi `docs/adr/` pour les décisions structurantes détaillées.

## Processus

Un seul processus résident `NexusDesk.exe` (utilisateur standard) au lot 0 : icône de zone
de notification, fenêtre principale créée au démarrage, instance unique via mutex nommé
`Local\NexusDesk` (ADR-0002). L'assistant élevé (`NexusDesk.Elevated.exe`) n'existe pas
encore (prévu lot 7, ADR-0001).

## Couches et règles de dépendance

| Couche | Dossier | Peut importer (direct) | Ne doit jamais importer (direct) |
| --- | --- | --- | --- |
| Interface | `ui/` | `viewmodels/`, `core/` | `integrations/`, `database/` |
| Présentation | `viewmodels/` | `services/`, `core/` | `ui/`, `integrations/` |
| Métier | `services/` | `repositories/`, `core/` | Qt, `ui/`, `integrations/` |
| Données | `repositories/`, `database/` | `models/`, `core/` | `services/`, `ui/` |
| Intégrations | `integrations/` | `core/` | `services/`, `ui/` |

Ces règles sont vérifiées par `import-linter` (`pyproject.toml`, section
`[tool.importlinter]`) avec `allow_indirect_imports = true` : ce qui est interdit, c'est
qu'un module d'une couche importe **directement** un module d'une couche non autorisée — pas
qu'il en dépende transitivement via la chaîne normale (ex. `ui` dépend bien de `database` au
bout du compte, mais seulement via `viewmodels -> services -> repositories`, jamais par un
import direct).

`app.py` est la racine de composition : seul module autorisé à importer toutes les couches
pour les assembler (`Application.__init__`).

## Gestionnaire de tâches (`core/tasks.py`)

`TaskManager` encapsule une instance dédiée de `QThreadPool`. Chaque tâche :
- a une clé de déduplication (deux tâches identiques ne peuvent pas tourner en même temps) ;
- reçoit un `CancellationToken` et un `ProgressReporter` (débit borné à ~10 mises à jour/s) ;
- ne laisse jamais d'exception s'échapper de `QRunnable.run()` : toute erreur est capturée et
  republiée via le signal `failed`, typée (`DependencyMissing`, `PermissionDenied`,
  `Timeout`, `Cancelled`) quand elle vient de `core/errors.py`, sinon l'exception d'origine.

## Base de données (`database/`)

Deux bases SQLite sous `%LOCALAPPDATA%\NexusDesk\data\` : `nexusdesk.db` (paramètres et,
plus tard, inventaires/événements/OCR/presse-papiers/scans) et `metrics.db` (mesures réseau,
créée dès le lot 0 mais sans schéma Alembic encore, ADR-0008). Mode WAL,
`foreign_keys=ON`, `busy_timeout=5000`, `synchronous=NORMAL` sur chaque connexion
(`database/engine.py`). Toute écriture passe par une file unique
(`database/write_queue.py`, ADR-0007) pour éviter les verrous SQLite entre fils de travail.

Migrations (`database/migration_runner.py`) : invocation programmatique d'Alembic au
démarrage. Si une migration est nécessaire, sauvegarde + `PRAGMA integrity_check` avant la
tentative ; en cas d'échec, restauration de la sauvegarde et démarrage en lecture seule
(jamais de perte de données). Testé par `tests/integration/database/`.

## Design system (`ui/theme/`)

Jetons (`tokens.py`) → génération QSS (`qss_builder.py`, ADR-0004) → application par
`ThemeManager` (thème sombre/clair/suivre Windows, effet Mica avec repli silencieux si
indisponible). Les icônes SVG sont chargées via `QSvgRenderer` + composition `SourceIn`
(`icon_provider.py`), pas via `QIcon(chemin)`, pour éviter toute dépendance au plugin Qt
`iconengines` dans l'exécutable packagé.

## Shell (`ui/shell/`)

`MainWindow` : navigation latérale repliable (`NavigationSidebar`), raccourcis `Ctrl+1` à
`Ctrl+7` (tableau de bord + 6 modules), `Paramètres`/`Diagnostic` accessibles par boutons
dédiés. La croix réduit dans le tray par défaut (ADR-0006).

## DiskPilot (`services/diskpilot/`, `ui/pages/diskpilot/`) — Lot 1

Premier module métier réel (`services/` était vide au lot 0). Flux de bout en bout :

- **Scan** (`services/diskpilot/scanner.py`) : parcours itératif à pile explicite sur
  `os.scandir` (jamais `os.walk`/récursion profonde). `os.stat()` (pas `DirEntry.stat()` mis
  en cache, qui ne reporte jamais `st_nlink` correctement sous Windows) + détection des liens
  physiques conditionnelle (`st_nlink > 1` seulement, ADR-0011) pour tenir le budget d'1M de
  fichiers en moins de 3 minutes. Jonctions/symlinks jamais suivis, seulement enregistrés
  (`DiskLinkEntry`). Fichiers OneDrive à la demande jamais ouverts ni lus (détection par
  masque d'attributs `FILE_ATTRIBUTE_RECALL_ON_OPEN`/`RECALL_ON_DATA_ACCESS`).
- **Doublons** (`duplicate_finder.py`) : regroupement par taille exacte → empreinte
  partielle (64 Ko tête/queue) → empreinte complète, avec cache persistant par
  `(chemin, taille, date de modification)`.
- **Suppression** (`deletion_service.py`) : revérification taille/date juste avant l'envoi à
  la Corbeille (`build_preview`), refus systématique des fichiers système/exclus/verrouillés
  (`filter_refused`), délégation au port `SendToRecycleBin` (jamais d'appel Windows direct
  depuis `services/`). Suppression **définitive** non câblée ce lot (réglage
  `permanent_delete_enabled` existe, décoché par défaut).
- **Persistance** (`repositories/diskpilot_scan_repository.py` et consorts) : dossiers
  persistés jusqu'à la profondeur 4, 1000 plus gros fichiers par scan, échantillon de 5000
  entrées ignorées — les compteurs agrégés (`DiskScan.file_count`, etc.) ne sont jamais
  tronqués. Rétention des 5 derniers scans `completed` par racine via `DELETE` + cascade FK
  (ADR-0013), auto-guérison d'un scan `running` orphelin au démarrage
  (`mark_stale_running_as_failed`).
- **Cache d'empreintes** : base SQLite séparée (`diskpilot_hash_cache.db`), hors chaîne
  Alembic, sa propre `WriteQueue` (ADR-0015).
- **Interface** (`ui/pages/diskpilot/`, ADR-0012) : sous-paquet avec un panneau par
  sous-vue, widget `TreemapWidget` (algorithme squarifié de Bruls/Huizing/van Wijk, mise en
  page mise en cache, recalculée seulement au redimensionnement ou à un nouveau dossier
  affiché — jamais à chaque `paintEvent`, jamais rafraîchie pendant un scan en direct).
  `DeletionDialog` modale partagée par tous les panneaux qui proposent une suppression,
  ce qui sérialise naturellement l'usage du `DeletionViewModel` partagé sans qu'aucun
  panneau n'ait à filtrer les signaux déclenchés par un autre.
- **Corbeille** : `SHFileOperation` plutôt que `IFileOperation` (ADR-0010), appelé fichier
  par fichier pour un rapport d'échec partiel fiable.
