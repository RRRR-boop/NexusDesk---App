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

## Lot 1 — DiskPilot

Toujours en utilisateur standard, aucune élévation :

| Opération | Privilège requis | Mécanisme |
| --- | --- | --- |
| Lister les volumes et leur espace libre | Aucun | `psutil.disk_partitions`/`disk_usage`, `win32api.GetVolumeInformation` |
| Parcourir un dossier (scan) | Aucun (accès refusé par entrée est signalé, jamais bloquant) | `os.scandir`/`os.stat` en utilisateur standard |
| Envoyer un fichier à la Corbeille | Aucun | `SHFileOperation` + `FOF_ALLOWUNDO` (ADR-0010) |
| Suppression **définitive** | Non câblée ce lot | Réglage `permanent_delete_enabled` existe, décoché par défaut |
| Ouvrir l'Explorateur / l'Assistant Stockage Windows | Aucun | `subprocess.run([explorer.exe, ...])`, jamais `shell=True` |

Les dossiers système par défaut (`$Recycle.Bin`, `System Volume Information`, `Recovery`,
et sur le volume système `Windows`/`Program Files*`/`ProgramData`) sont exclus par défaut du
scan — pas parce qu'ils exigeraient une élévation, mais pour éviter de scanner des données
sans valeur pour l'utilisateur. La racine explicitement choisie par l'utilisateur est
exemptée de cette règle (avec avertissement affiché), les exclusions imbriquées restant
actives pour tout chemin différent de la racine.
