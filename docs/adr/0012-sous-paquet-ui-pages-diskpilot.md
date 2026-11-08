# ADR-0012 — Restructuration en sous-paquet `ui/pages/diskpilot/`

## Statut
Décidé (choix réversible, section 21.3).

## Contexte
Les modules du lot 0 (Dashboard, AppManager, NetWatch...) sont de simples pages vides
(`PlaceholderPage`) et vivent chacune dans un unique fichier plat sous `ui/pages/`. DiskPilot
est le premier module avec une interface réellement riche : 6 sous-vues (volumes, scan et
treemap, plus gros fichiers, doublons, nettoyage, historique), un widget personnalisé
(treemap squarifié avec `QPainter`), et une boîte de dialogue de confirmation partagée.
Tout regrouper dans un seul fichier `diskpilot_page.py` de plusieurs centaines de lignes
rendrait le module difficile à parcourir et à faire évoluer indépendamment par sous-vue.

## Décision
`ui/pages/diskpilot_page.py` (le stub plat du lot 0) est remplacé par un sous-paquet
`ui/pages/diskpilot/` : un fichier par panneau (`volumes_panel.py`, `scan_panel.py`,
`largest_files_panel.py`, `duplicates_panel.py`, `cleanup_panel.py`, `history_panel.py`),
`treemap_widget.py` pour l'algorithme de mise en page squarifiée et le widget `QPainter`,
`deletion_dialog.py` pour la boîte de dialogue de suppression partagée entre panneaux, et
`page.py` qui assemble tout dans un `QTabWidget`. `__init__.py` ré-exporte `DiskPilotPage`
pour que `app.py` continue d'importer `from nexusdesk.ui.pages.diskpilot import DiskPilotPage`
sans changement de forme par rapport aux autres pages.

**Règle retenue pour les lots suivants** : un module reste un fichier plat tant qu'il n'a
besoin que d'un seul widget simple (comme les modules encore en `PlaceholderPage`) ; il
devient un sous-paquet dès qu'il a réellement besoin de plusieurs fichiers de widgets
distincts (sous-vues multiples, widget personnalisé, boîte de dialogue partagée) — jamais en
anticipation d'un besoin hypothétique futur.

## Conséquences
- Chaque panneau reste testable et lisible indépendamment (ex. `treemap_widget.py` ne connaît
  que l'algorithme de mise en page et le rendu, pas la logique de navigation par
  fil d'Ariane qui reste dans `scan_panel.py`).
- `page.py` reste un simple assembleur (QTabWidget + distribution du résultat de scan aux
  autres panneaux) : aucune logique métier n'y est dupliquée.
- Aucun contrat `import-linter` n'est affecté : le sous-paquet reste entièrement sous
  `nexusdesk.ui`, donc toujours soumis à la même règle (jamais d'import direct de
  `integrations`/`database`).
