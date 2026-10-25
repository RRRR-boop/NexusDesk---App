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
