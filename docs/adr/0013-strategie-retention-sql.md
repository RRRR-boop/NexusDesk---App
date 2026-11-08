# ADR-0013 — Stratégie de rétention SQL pour l'historique des scans

## Statut
Décidé (choix réversible, section 21.3).

## Contexte
Le cahier des charges demande de ne conserver que les 5 derniers scans complets par dossier
racine (section 11), pour éviter une croissance illimitée de `nexusdesk.db` au fil des scans
répétés. Chaque scan a jusqu'à 4 tables enfants (`diskpilot_folder_snapshot`,
`diskpilot_largest_file`, `diskpilot_skipped_entry`, `diskpilot_link_entry`,
`diskpilot_duplicate_group`/`diskpilot_duplicate_file`) pouvant compter plusieurs milliers de
lignes pour un scan de dossier volumineux.

## Options considérées
- **Boucle ORM** : charger les scans à purger en objets Python, puis appeler
  `session.delete(scan)` sur chacun en comptant sur les relations SQLAlchemy en cascade.
  Coûteux (charge chaque ligne enfant en mémoire pour la supprimer une par une) et fragile
  si une relation ORM n'est pas déclarée pour une des tables enfants.
- **`DELETE` SQL typé + cascade FK** : une seule requête `DELETE FROM diskpilot_scan WHERE ...`
  ciblant les lignes `diskpilot_scan` à purger ; la cascade est déléguée à SQLite
  (`ON DELETE CASCADE` sur chaque FK enfant, `PRAGMA foreign_keys=ON` déjà actif sur chaque
  connexion, `database/engine.py`).

## Décision
`repositories/diskpilot_scan_repository.py::_prune_locked` exécute un `DELETE` SQLAlchemy
typé sur `diskpilot_scan`, restreint par une sous-requête `ORDER BY started_at DESC LIMIT 5`
qui désigne les scans `completed` à conserver pour la racine normalisée concernée. La
cascade FK supprime automatiquement toutes les lignes enfants des scans purgés, en une seule
transaction, sans boucle ORM. Un second `DELETE` supprime également tout scan
`cancelled`/`failed` précédent pour la même racine dès qu'un nouveau scan démarre pour
celle-ci (ces scans n'ont pas vocation à persister au-delà du scan suivant).

## Conséquences
- Purge en une seule requête par catégorie de statut, peu importe le nombre de lignes
  enfants — pas de coût proportionnel au volume de données du scan purgé côté application
  Python (le travail est fait par SQLite lui-même).
- Testé par insertion réelle de 7 scans complets pour une même racine puis vérification que
  seuls les 5 plus récents restent ET que les tables enfants des scans purgés sont bien
  vides (`tests/unit/repositories/test_diskpilot_scan_repository.py`).
- Dépend strictement de `PRAGMA foreign_keys=ON` sur la connexion SQLite ; ce réglage est
  déjà appliqué systématiquement par `database/engine.py` (ADR implicite du lot 0), donc
  aucune dépendance nouvelle introduite par ce lot.
