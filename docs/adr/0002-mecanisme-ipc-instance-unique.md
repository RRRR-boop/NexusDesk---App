# ADR-0002 — Mécanisme IPC de l'instance unique

## Statut
Décidé (choix réversible, section 21.3).

## Contexte
Une seule instance de NexusDesk doit tourner à la fois (mutex nommé `Local\NexusDesk`). Un
second lancement doit transmettre sa demande (ouvrir la fenêtre principale) à l'instance
existante puis se terminer rapidement, sans jamais créer de `QApplication` inutile.

## Options considérées
- **Tube nommé (named pipe) via pywin32** : déjà une dépendance du projet, ACL contrôlable
  précisément (DACL restreinte au SID de l'utilisateur courant), protocole textuel simple et
  extensible.
- **`FindWindow` + `WM_COPYDATA`** : fonctionne, mais fragile (dépend de trouver la bonne
  fenêtre top-level, pas de contrôle d'accès fin).
- **Socket TCP loopback** : fonctionne sur toutes plateformes mais ouvre un port local,
  inutilement visible pour un canal strictement local.
- **Fichier surveillé (polling)** : latence, complexité pour éviter les races.

## Décision
Tube nommé `\\.\pipe\NexusDesk`, créé côté instance primaire avec une DACL limitée au SID de
l'utilisateur courant (`integrations/windows/single_instance.py`). Protocole : chaîne UTF-8
brute envoyée en un seul `WriteFile`, réponse `ACK`. Deux commandes au lot 0 :
`OPEN_MAIN_WINDOW` et `QUIT` (ADR-0009). Le handle du mutex est conservé en attribut
d'instance de longue durée (`SingleInstanceGuard`), jamais dans une variable locale, pour
éviter qu'il soit refermé silencieusement par le ramasse-miettes.

## Conséquences
- pywin32 reste une dépendance obligatoire (déjà prévue section 3).
- Le même mécanisme pourra transporter les futures commandes de la palette (« Scanner
  Téléchargements » depuis un second lancement, etc.) sans changer d'architecture.
