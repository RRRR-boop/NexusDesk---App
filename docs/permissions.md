# Permissions requises

## Lot 0

NexusDesk tourne entièrement en **utilisateur standard**, sans élévation :

| Opération | Privilège requis | Mécanisme |
| --- | --- | --- |
| Mutex nommé (instance unique) | Aucun | `Local\NexusDesk`, portée session utilisateur |
| Tube nommé (relais de commandes) | Aucun | DACL restreinte au SID de l'utilisateur courant |
| Lecture/écriture `%LOCALAPPDATA%\NexusDesk` | Aucun | Dossier appartenant à l'utilisateur courant |
| Clé `HKCU\...\Run` (lancement au démarrage) | Aucun | Ruche `HKEY_CURRENT_USER`, pas `HKLM` |
| Effet Mica (`DwmSetWindowAttribute`) | Aucun | API DWM accessible en utilisateur standard |

Aucune fonction du lot 0 n'exige l'administrateur. L'assistant élevé
(`NexusDesk.Elevated.exe`, ADR-0001) n'existe pas encore : il arrivera au lot 7 pour les
opérations qui exigent réellement `HKLM`, le journal Security, ou une désinstallation
machine — chacune signalée par une icône de bouclier avant le clic (section 2).
