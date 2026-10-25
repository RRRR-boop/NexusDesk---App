# ADR-0007 — File d'écriture SQLite unique

## Statut
Décidé (le principe est imposé section 4 ; le mécanisme précis est réversible).

## Contexte
« Chaque fil de travail ouvre sa propre session SQLAlchemy ; les écritures passent par une
file unique pour éviter les verrous SQLite. » Il faut choisir comment implémenter cette file.

## Options considérées
- **`QThread` Qt dédié** : s'intègre à l'écosystème de signaux Qt, mais lie ce composant
  purement infrastructure au cycle de vie d'un `QApplication`, compliquant les tests
  unitaires isolés.
- **`threading.Thread` démon + `queue.Queue`** : composant infrastructure pur, testable sans
  `QApplication`, suffisant puisque la file n'a besoin d'aucune boucle d'événements Qt.

## Décision
`database/write_queue.py` : un `threading.Thread` démon unique consomme une
`queue.Queue[(fonction, Future)]`. Chaque tâche métier qui écrit appelle
`WriteQueue.submit_write(fn)` et récupère un `concurrent.futures.Future` pour, si besoin,
attendre le résultat de manière synchrone (ex. `SettingsRepository.set`). Chaque exécution
passe par `session_scope()` (une transaction par opération métier).

## Conséquences
- Arrêt propre : `WriteQueue.stop(timeout)` pousse un sentinel `None`, attend la fin du
  thread, borné à 3 s (critère de sortie section 20).
- Les lots futurs (ClipVault, DiskPilot...) doivent écrire via cette même file, jamais
  directement sur une session ouverte depuis un `QRunnable`.
