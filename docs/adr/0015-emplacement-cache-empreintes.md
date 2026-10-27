# ADR-0015 — Emplacement du cache d'empreintes de doublons

## Statut
Décidé (choix réversible, section 21.3).

## Contexte
La détection de doublons (section 11) a besoin d'une empreinte SHA-256 (partielle puis
complète) par fichier candidat, mise en cache par `(chemin, taille, date de modification)`
pour éviter de relire et rehacher un fichier inchangé entre deux scans. Cette donnée est
entièrement **dérivée** du contenu réel des fichiers sur disque : elle peut être reconstruite
à tout moment, perdue sans dommage, et n'a aucune valeur métier propre (contrairement aux
scans eux-mêmes, qui sont un historique que l'utilisateur consulte).

## Options considérées
- **Table dans `nexusdesk.db`**, suivant la même chaîne de migrations Alembic que les autres
  tables DiskPilot : cohérent avec le reste du schéma, mais fait porter une migration
  versionnée à une donnée purement jetable, et grossit le fichier de sauvegarde principal
  (`database/backup.py` sauvegarde `nexusdesk.db` avant chaque migration) sans bénéfice.
- **Fichier SQLite séparé** (`diskpilot_hash_cache.db`, sous `core/paths.get_cache_dir()`),
  hors de la chaîne Alembic principale, créé directement via
  `CacheBase.metadata.create_all(engine)` : séparation claire entre donnée durable
  (historique des scans) et donnée dérivée/jetable (cache d'empreintes), peut être supprimée
  par l'utilisateur sans perte fonctionnelle (juste un recalcul au prochain scan).

## Décision
Le cache d'empreintes vit dans son propre fichier SQLite (`diskpilot_hash_cache.db`) sous
`core/paths.get_cache_dir()`, avec sa propre base déclarative (`models/diskpilot_cache.py::CacheBase`,
distincte de `models/base.py::Base`), créé par un `CacheBase.metadata.create_all(engine)`
direct dans `app.py` plutôt que par une révision Alembic. Il a sa **propre** `WriteQueue`
(symétrique à celle de `nexusdesk.db`), pour respecter littéralement la règle « toute
écriture SQLite passe par la file unique » appliquée par moteur.

## Conséquences
- `nexusdesk.db` ne grossit jamais à cause du cache de hachage, et les sauvegardes
  pré-migration (`database/backup.py`) restent limitées aux données réellement durables.
- Supprimer `diskpilot_hash_cache.db` (ex. nettoyage manuel par l'utilisateur, ou en cas de
  corruption) ne casse rien : `DiskPilotHashCacheRepository.get` renvoie simplement `None`,
  et les empreintes sont recalculées au prochain scan.
- Deux moteurs SQLite, deux files d'écriture, deux `dispose()`/`stop()` à l'arrêt de
  l'application (`Application._shutdown`) — complexité additionnelle acceptée car elle reste
  localisée à `app.py` (racine de composition) et ne fuit vers aucune autre couche.
