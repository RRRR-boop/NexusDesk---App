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

Les engagements relatifs à ClipVault (chiffrement DPAPI, exclusions, détection de secrets)
et à ScreenText (historique chiffré) seront documentés ici à partir des lots 4 et 5, quand
ces modules existeront réellement.
