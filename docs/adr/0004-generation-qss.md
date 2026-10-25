# ADR-0004 — Génération du QSS par assemblage Python natif

## Statut
Décidé (choix réversible, section 21.3).

## Contexte
Le design system (section 5) exige que les jetons (`ui/theme/tokens.py`) soient la seule
source de vérité des couleurs, tailles et espacements, et que les feuilles QSS en soient
*générées* plutôt qu'écrites à la main avec des valeurs codées en dur.

## Options considérées
- **Moteur de templates (Jinja2)** : lisible, mais ajoute une dépendance absente de la stack
  retenue section 3, pour un besoin qui reste un simple remplacement de variables dans des
  f-strings.
- **Assemblage Python natif (f-strings)** : zéro dépendance supplémentaire, un seul endroit
  (`ui/theme/qss_builder.py`) qui transforme les jetons en règles QSS.

## Décision
Assemblage par f-strings dans `build_qss(colors, density, text_size) -> str`. Chaque règle
QSS référence exclusivement des valeurs issues de `tokens.py` ; aucun widget du reste de
l'application ne doit contenir de couleur ou de taille codée en dur (vérifié par revue de
code, pas par un outil automatique au lot 0).

## Conséquences
- Pas de nouvelle dépendance à justifier dans `docs/dependances.md`.
- Ajouter un composant QSS revient à ajouter un bloc de règles dans `qss_builder.py`.
