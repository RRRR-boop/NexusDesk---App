# NexusDesk

Boîte à outils Windows 11 locale, gratuite et sans télémétrie, réunissant six modules (AppManager,
NetWatch, ScreenText, LogDoctor, DiskPilot, ClipVault) autour d'un tableau de bord, d'une palette de
commandes et d'une recherche globale.

Le cahier des charges complet se trouve dans `reports/` (hors dépôt). Le projet est livré par lots ; l'état
d'avancement est consigné dans `docs/journal-des-lots.md`.

## Développement

```powershell
./scripts/install-dev.ps1   # prépare l'environnement (uv, Python 3.12, hooks pre-commit)
./scripts/run.ps1 -Dev       # lance l'application depuis les sources
./scripts/check.ps1          # Ruff, mypy --strict, import-linter, pip-audit
./scripts/test.ps1 -Coverage # tests unitaires + couverture
./scripts/build.ps1          # empaquetage PyInstaller (mode dossier)
```

## Architecture

Voir `docs/architecture.md` et les décisions consignées dans `docs/adr/`.
