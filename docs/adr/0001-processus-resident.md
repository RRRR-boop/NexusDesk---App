# ADR-0001 — Processus résident + assistant élevé séparé

## Statut
Imposé par le cahier des charges (section 4), consigné ici pour mémoire et pour la suite.

## Contexte
Un seul processus Python ne peut pas s'élever en cours de route (erreur technique corrigée
depuis la v1). NexusDesk doit pourtant tourner en utilisateur standard pour l'usage courant
tout en pouvant exécuter, à la demande, des opérations qui exigent l'administrateur (journal
Security, clé `HKLM\...\Run`, désinstallation machine).

## Décision
NexusDesk tourne en un processus résident `NexusDesk.exe` (utilisateur standard). Un second
exécutable `NexusDesk.Elevated.exe`, lancé via `ShellExecuteEx`/`runas` seulement quand une
opération l'exige, portera la liste fermée de commandes privilégiées. Il n'existe pas encore
au lot 0 (prévu lot 7), mais l'architecture ne doit rien faire qui l'empêcherait d'être
ajouté sans refonte :
- le canal de communication inter-processus du lot 0 (tube nommé, ADR-0002) suit déjà le
  même modèle (ACL restreinte au SID utilisateur, protocole textuel simple) que celui prévu
  pour l'assistant élevé ;
- aucune logique métier du lot 0 ne suppose des droits administrateur.

## Conséquences
- Le lot 0 livre uniquement le processus résident.
- Le lot 7 ajoutera `elevated/` sans modifier la structure des couches existantes.
