# Confidentialité

## Lot 0

- Aucune donnée ne quitte le PC : le lot 0 ne fait aucun appel réseau sortant.
- Aucune télémétrie, aucun compte, aucun identifiant envoyé où que ce soit.
- Les journaux techniques (`%LOCALAPPDATA%\NexusDesk\logs\`) ne contiennent jamais le chemin
  complet du profil utilisateur : il est systématiquement remplacé par `%USERPROFILE%`
  avant écriture (`core/logging_setup.py`).
- Les paramètres stockés (onglets Général et Apparence) ne contiennent aucune donnée
  personnelle : thème, densité, comportement de la croix, etc.
- Le tube nommé utilisé pour l'instance unique (ADR-0002) a sa DACL restreinte au SID de
  l'utilisateur courant : aucun autre compte Windows ne peut y lire ou écrire.

## Lot 1 — DiskPilot

- Aucun appel réseau : la liste des volumes, le scan, la détection de doublons et la
  suppression sont strictement locaux.
- Les fichiers OneDrive à la demande (placeholders) ne sont **jamais** ouverts ni lus : leur
  statut est déterminé uniquement par un masque d'attributs déjà fourni par le système de
  fichiers, ce qui évite tout téléchargement involontaire déclenché par l'analyse.
- Les chemins de fichiers scannés sont conservés dans `nexusdesk.db` (historique des 5
  derniers scans par dossier) pour permettre comparaison et export CSV — jamais transmis
  hors de la machine. Le cache d'empreintes (`diskpilot_hash_cache.db`) ne stocke que des
  empreintes SHA-256, jamais le contenu des fichiers.
- Aucune suppression définitive dans ce lot : seule la Corbeille Windows (récupérable) est
  utilisée.

Les engagements relatifs à ClipVault (chiffrement DPAPI, exclusions, détection de secrets)
et à ScreenText (historique chiffré) seront documentés ici à partir des lots 4 et 5, quand
ces modules existeront réellement.
