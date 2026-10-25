# ADR-0006 — Comportement de la croix de fermeture

## Statut
Décidé (le principe est imposé section 6 ; le détail d'implémentation est réversible).

## Contexte
NexusDesk doit tourner fenêtre fermée (ClipVault, raccourci OCR...). La croix de la fenêtre
ne doit donc pas quitter l'application par défaut, mais l'utilisateur doit pouvoir choisir le
comportement inverse (section 15, onglet Général).

## Décision
`MainWindow.closeEvent` consulte `close_behavior` (`"minimize"` par défaut) :
- `"minimize"` : `event.ignore()` puis `hide()`. Une notification (`minimized_to_tray`) n'est
  émise que la **première fois** par session, pour ne pas être répétitive (section 6).
- `"quit"` : `event.accept()`, ce qui laisse la séquence d'arrêt normale de Qt se dérouler.

L'état « notification déjà affichée » est un booléen en mémoire (`_first_minimize_notified`),
pas persisté : il se réinitialise à chaque démarrage, ce qui est acceptable puisque
l'information n'a de sens que pour la session en cours.

## Conséquences
- `qt_app.setQuitOnLastWindowClosed(False)` est réglé dans `__main__.py` pour que masquer la
  fenêtre ne déclenche jamais une sortie implicite de la boucle Qt.
- Testé par `tests/ui/test_main_window.py` (masquage + notification unique, et chemin
  « quitter » sans notification).
