# Journal des modifications

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/). Le détail honnête
de chaque lot (fait, vérifié, non vérifié, limites) est dans `docs/journal-des-lots.md`.

## [0.2.1-beta.3] — 2026-11-08 — Préversion

Remplace les préversions 0.2.1-beta.1 et 0.2.1-beta.2, retirées car défectueuses.

### Corrigé

- **DiskPilot dans l'exécutable** : l'analyse échouait avec « No module named
  'win32timezone' » dès qu'un dossier contenait un fichier à liens physiques (fréquent :
  environnements Python, caches de paquets, dossiers synchronisés). pywin32 importe ce module
  à l'exécution, invisible pour PyInstaller ; il est désormais embarqué explicitement.
- **Icône** : l'exécutable, l'installateur, les raccourcis et la barre des tâches affichaient
  l'icône générique de Python/Qt. Ils utilisent désormais l'icône NexusDesk (fichier `.ico`
  multirésolution, 16 à 256 px).

### Ajouté

- `scripts/make_icon.py` (génération de `app.ico`) et tests de non-régression sur la
  configuration d'empaquetage (`tests/unit/test_packaging.py`).

## [0.2.1-beta.2] — 2026-11-08 — Préversion (retirée)

Aucune modification fonctionnelle par rapport à 0.2.1-beta.1 : cette version intègre
correctement la licence.

### Modifié

- Licence : NexusDesk est désormais distribué sous **GNU GPL v3** (`GPL-3.0-only`, fichier
  `LICENSE`) au lieu d'une licence propriétaire. La préversion 0.2.1-beta.1 a été publiée
  alors que ses métadonnées indiquaient encore « Proprietary ».
- Noms des fichiers de distribution : `NexusDesk-v<version>-Setup.exe` et
  `NexusDesk-v<version>-portable.zip`.

### Ajouté

- Texte intégral de la GNU GPL v3 (`LICENSE`) dans l'installateur (page « Contrat de
  licence » et dossier d'installation) et dans l'archive portable.
- `THIRD-PARTY-LICENSES.txt` : avis et textes de licence de l'interpréteur Python et de chaque
  composant tiers embarqué (PySide6/Qt sous LGPL v3, SQLAlchemy, Alembic, pydantic, psutil,
  pywin32…), avec le lien vers le code source correspondant.
- Métadonnées Windows de `NexusDesk.exe` et de l'installateur (Propriétés → Détails) : nom,
  version, éditeur, licence.
- `SHA256SUMS.txt` aux fins de ligne LF, vérifiable aussi par `sha256sum -c`.

## [0.2.1-beta.1] — 2026-11-08 — Préversion (retirée)

Première version distribuée : socle (lot 0) et module DiskPilot (lot 1). Les cinq autres
modules affichent une page « Module à venir » et ne proposent aucune fonction.

### Ajouté

- Onglet **Paramètres → DiskPilot** : taille minimale des doublons, seuils d'avertissement et
  d'alerte d'espace libre, **dossiers exclus des analyses** (ajout par sélection de dossier,
  retrait, sans doublon). Tous ces réglages s'appliquent sans redémarrage.
- Exclusions personnalisées réellement appliquées par le scan (elles existaient dans le
  schéma mais n'étaient lues par aucun code) ; elles sont comptées à part
  (`excluded_user`) dans les éléments ignorés.
- Distribution : archive portable ZIP (mode portable : données à côté de l'exécutable),
  installateur Windows par utilisateur sans droits administrateur (Inno Setup), `VERSION.txt`,
  `SHA256SUMS.txt`, script `scripts/package-release.ps1`.

### Corrigé

- Tout changement dans les onglets Général ou Apparence réécrivait en base les réglages
  DiskPilot à leurs valeurs par défaut.
- Analyser explicitement un dossier exclu par défaut (par exemple `C:\Program Files`)
  renvoyait un résultat vide, contrairement au cahier des charges (section 11). Le scan
  liste désormais son contenu ; la **suppression reste refusée** pour tout fichier situé dans
  un dossier protégé (lecture seule).
- Avertissement de dépréciation Qt au démarrage (`AA_UseHighDpiPixmaps`, sans effet en Qt 6).

### Limites connues

- Performance : environ 3 200 à 5 600 fichiers/s mesurés (369 112 fichiers de
  `C:\Program Files` en 66 à 114 s selon le cache disque), soit environ 3 à 5 min pour
  1 million de fichiers au lieu des 3 min visées. La protection temps réel de l'antivirus
  ralentit fortement et de façon variable les grosses analyses.
- Mémoire : environ 1,1 Ko par fichier ou dossier analysé (≈ 450 Mo pour 410 000 entrées,
  ≈ 1,1 Go estimés pour 1 million) pendant l'affichage d'un scan.
- Suppression définitive non disponible : les fichiers vont toujours à la Corbeille.
- Fichiers OneDrive à la demande : détection testée sur la logique, pas avec un vrai client
  OneDrive.
- Non vérifiés : Narrateur Windows, mise à l'échelle DPI mixte et multi-écran, rendu visuel
  de l'effet Mica.
- Exécutable non signé : Windows SmartScreen peut afficher un avertissement au premier
  lancement.

## [0.2.0] — 2026-10-27 — Lot 1, non distribué

Module DiskPilot : volumes, scan (liens physiques, jonctions, OneDrive à la demande), treemap,
plus gros fichiers, doublons avec cache d'empreintes, suggestions de nettoyage, envoi à la
Corbeille, historique et comparaison, export CSV.

## [0.1.0] — 2026-10-25 — Lot 0, non distribué

Socle : architecture en couches, SQLite + Alembic avec sauvegarde et restauration, gestionnaire
de tâches, instance unique, zone de notification, design system clair/sombre, paramètres,
diagnostic, empaquetage PyInstaller.
