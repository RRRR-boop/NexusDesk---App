# Dépendances

Toute nouvelle dépendance doit être ajoutée ici avec son rôle, sa licence et l'alternative
écartée (section 3 et section 21.7). Les dépendances ci-dessous sont celles introduites par
le Lot 0.

| Dépendance | Rôle | Licence | Alternative écartée |
| --- | --- | --- | --- |
| `pyside6` | Interface Qt Widgets (fenêtres, widgets, QSS, SVG) | LGPLv3 (liaison dynamique) | PyQt6 (licence commerciale ou GPL pour l'usage libre) |
| `sqlalchemy` | ORM typé, accès aux données via les dépôts | MIT | Requêtes SQL brutes (pas de typage, risque d'injection) |
| `alembic` | Migrations de schéma versionnées | MIT | Scripts SQL maison (pas de suivi de version standard) |
| `pydantic` | Validation des schémas de paramètres | MIT | `dataclasses` nues (pas de validation) |
| `pydantic-settings` | Chargement/validation de configuration | MIT | Lecture manuelle de fichiers de config |
| `pywin32` | Mutex nommé, tube nommé, DACL, DWM (Mica), registre | PSF / licence pywin32 | `ctypes` seul (plus verbeux pour la sécurité des tubes) |
| `pyinstaller` | Empaquetage en exécutable (mode dossier) | GPL avec exception | `cx_Freeze` (moins mature sur Windows pour PySide6) |
| `ruff` | Lint + formatage | MIT | `flake8` + `black` séparés (plus lent, deux outils) |
| `mypy` | Vérification de types stricte | MIT | `pyright` (écarté pour rester dans l'écosystème pip/uv) |
| `pytest`, `pytest-qt`, `pytest-cov`, `hypothesis` | Tests unitaires, interface, couverture, propriétés | MIT / MPL 2.0 | `unittest` nu (moins d'outillage) |
| `import-linter` | Vérification automatique des règles de couches (section 4) | MIT | Revue de code seule (non automatisée, donc oubliable) |
| `pre-commit` | Hooks Git (lint, format, types) | MIT | Scripts Git hooks maison |
| `pip-audit` | Audit de vulnérabilités des dépendances | Apache 2.0 | `safety` (base de données moins ouverte) |
| `pip-licenses` | Inventaire des licences tierces | MIT | Vérification manuelle (source d'erreur) |
| `types-pywin32` | Annotations de types pour mypy --strict sur pywin32 | PSF | `# type: ignore` généralisé (perte de vérification) |

## Choix écartés (section 3)

- **Qt Charts** : GPLv3 dans sa version libre, contrairement au cœur de Qt. Remplacé par
  `pyqtgraph` quand les graphiques seront nécessaires (lot 2).
- **pytesseract** : simple surcouche de sous-processus ; un appel direct à `tesseract.exe`
  avec arguments en liste suffira (lot 5), retire une dépendance.
- **PyQt-Fluent-Widgets** : sous GPLv3 pour un usage libre ; design system maison sur QSS
  (ADR-0004) à la place.
- **asyncio + qasync** : un seul modèle de concurrence retenu (`QThreadPool` +
  `core/tasks.py`), pour éviter de mélanger deux boucles d'événements.
- **Jinja2** : écarté pour la génération QSS (ADR-0004), assemblage Python natif à la place.
