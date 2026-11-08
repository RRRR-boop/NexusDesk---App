# ADR-0010 — Substitution de `SHFileOperation` à `IFileOperation`

## Statut
Décidé (choix réversible, section 21.3).

## Contexte
Le cahier des charges (section 11) cite `IFileOperation` (interface COM moderne, Vista+)
pour envoyer des fichiers à la Corbeille. `IFileOperation` nécessite soit `comtypes` (nouvelle
dépendance), soit un appel COM manuel via `ctypes` relativement verbeux pour un besoin aussi
simple que « envoyer N fichiers à la Corbeille et obtenir un résultat par fichier ».

## Options considérées
- **`IFileOperation` via `comtypes`** : API moderne, mais nouvelle dépendance tierce pour un
  seul besoin, et gestion d'erreurs par fichier plus complexe (callback `IFileOperationProgressSink`).
- **`win32com.shell.shell.SHFileOperation`** (déjà disponible via `pywin32`, déjà une
  dépendance du projet) : API plus ancienne (toujours supportée par Windows 11), mais un seul
  appel par fichier donne un code d'erreur Win32 par fichier sans callback.

## Décision
`integrations/windows/filesystem.py::send_to_recycle_bin` utilise `SHFileOperation` avec les
indicateurs `FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT`, **appelé fichier par fichier**
(pas un seul appel batché sur la liste complète) : un échec sur un fichier ne doit jamais
empêcher la suppression des autres, et le code de retour Win32 de chaque appel individuel est
directement exploitable sans callback.

## Conséquences
- Résultat observable identique à `IFileOperation` du point de vue utilisateur : suppression
  récupérable (Corbeille), jamais définitive dans ce lot.
- Pas de nouvelle dépendance (`pywin32` est déjà requis pour Mica, l'instance unique, etc.).
- Appeler un `SHFileOperation` par fichier plutôt qu'un seul appel sur la liste est plus lent
  pour un très grand nombre de suppressions simultanées ; acceptable car les suppressions
  DiskPilot restent des opérations ponctuelles décidées par l'utilisateur (dizaines à
  quelques centaines de fichiers), jamais un flux de masse.
- Si un futur lot a besoin de la richesse d'`IFileOperation` (ex. barre de progression native
  Windows pendant la suppression), cette décision est réversible sans changer le port
  `SendToRecycleBin` côté `services/`.
