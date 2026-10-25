# ADR-0008 — Création anticipée de metrics.db

## Statut
Décidé (choix réversible, section 21.3) — **affiné pendant l'implémentation** par rapport à
l'intention initiale du plan de lot.

## Contexte
Section 14 prévoit deux bases : `nexusdesk.db` (paramètres, inventaires, événements, OCR,
presse-papiers, scans) et `metrics.db` (mesures réseau brutes, écritures fréquentes,
isolées). NetWatch, qui remplira réellement `metrics.db`, n'arrive qu'au lot 2.

## Option envisagée puis écartée
Donner à `metrics.db` sa propre chaîne Alembic complète dès le lot 0 (environnement, dossier
`versions/`, révision initiale), uniquement pour prouver que le mécanisme de
migration/sauvegarde fonctionne sur les deux fichiers. Écartée : une révision Alembic qui ne
crée aucune vraie table n'est qu'un échafaudage sans fonction réelle, contraire à l'esprit de
la section 1 (« rien d'affiché ou de construit qui ne serve une fonction réelle »).

## Décision
`metrics.db` est créée et configurée (PRAGMA WAL/foreign_keys/busy_timeout/synchronous) dès
le lot 0 via le même `create_sqlite_engine()` que `nexusdesk.db`, mais **sans** chaîne
Alembic : elle n'a encore aucun schéma à versionner. Le mécanisme de sauvegarde
(`database/backup.py`) est générique et déjà testé sur un fichier SQLite quelconque
(`tests/unit/database/test_backup.py`) ; il s'appliquera à `metrics.db` sans modification
quand NetWatch (lot 2) y ajoutera sa première révision réelle.

## Conséquences
- Le dossier `data/` contient bien deux fichiers `.db` dès le lot 0, conformément à la
  structure de la section 14.
- Le lot 2 ajoutera une révision initiale pour `metrics.db` suivant le même schéma que
  `database/migrations/` pour `nexusdesk.db` (ou un script_location dédié si leurs chaînes de
  versions doivent diverger — à trancher au lot 2).
