# Journal des modifications

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/). Le détail honnête
de chaque lot (fait, vérifié, non vérifié, limites) est dans `docs/journal-des-lots.md`.

## [Non publié]

### Modifié

- Licence : NexusDesk est désormais distribué sous **GPL v3** (`GPL-3.0-only`, fichier
  `LICENSE`) au lieu d'une licence propriétaire. La préversion 0.2.1-beta.1 a été publiée
  alors que les métadonnées indiquaient encore « Proprietary ».

## [0.2.1-beta.1] — 2026-11-08 — Préversion

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
