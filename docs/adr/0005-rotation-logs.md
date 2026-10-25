# ADR-0005 — Rotation des journaux techniques par taille

## Statut
Décidé (choix réversible, section 21.3).

## Contexte
Section 14 : plafond de 5 fichiers de 5 Mo pour les journaux techniques.

## Options considérées
- **`TimedRotatingFileHandler`** (rotation périodique, ex. quotidienne) : taille non bornée
  entre deux rotations, imprévisible en espace disque.
- **`RotatingFileHandler`** (rotation par taille) : correspond directement au plafond fixé
  par le cahier des charges.

## Décision
`logging.handlers.RotatingFileHandler` avec `maxBytes=5*1024*1024` et `backupCount=4`
(fichier courant + 4 sauvegardes = 5 fichiers au total). Un filtre de formatage
(`_RedactingFormatter`) remplace le chemin du profil utilisateur par
`%USERPROFILE%` dans chaque ligne écrite, pour ne jamais faire fuiter de donnée
personnelle dans les journaux techniques.

## Conséquences
- Espace disque borné et prévisible (25 Mo maximum).
- Les lots suivants qui ajoutent de la journalisation (ClipVault, ScreenText...) doivent
  continuer à passer par ce même logger pour bénéficier de la rédaction automatique.
