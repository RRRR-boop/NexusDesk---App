# ADR-0009 — Commande IPC QUIT réservée aux tests

## Statut
Décidé (choix réversible, section 21.3).

## Contexte
`scripts/smoke-test.ps1` doit démarrer l'exécutable empaqueté puis le fermer proprement
*sans Python* (section 18 : validation possible dans un environnement sans Python). Il faut
un moyen de déclencher l'arrêt propre (annulation des tâches, file d'écriture, `dispose()`
des moteurs) depuis l'extérieur du processus.

## Décision
Une commande `QUIT` existe dans le protocole du tube nommé (`single_instance.py`), mais
n'est honorée par `Application._on_command_received` que si la variable d'environnement
`NEXUSDESK_ALLOW_IPC_QUIT=1` est présente au démarrage du processus. Elle n'est jamais
positionnée en usage normal — seul `scripts/smoke-test.ps1` la définit avant de lancer
l'exécutable. Un tiers qui parviendrait à écrire sur le tube (DACL restreinte au SID de
l'utilisateur courant, donc déjà limité) ne peut donc pas forcer l'arrêt de l'application en
usage normal.

## Conséquences
- `scripts/smoke-test.ps1` envoie `QUIT` via `System.IO.Pipes.NamedPipeClientStream` (.NET),
  sans dépendance à Python, conformément à la contrainte de validation en environnement
  vierge.
- Toute commande reçue hors de la liste fermée (`OPEN_MAIN_WINDOW`, `QUIT`) est ignorée.
