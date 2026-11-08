# PROJECT_HANDOVER.md — NexusDesk

> **Document de transmission complet.** Généré pour permettre la reprise du projet sur un
> autre ordinateur Windows, par une nouvelle instance Claude Code sans accès aux
> conversations précédentes.
>
> **Date de génération de ce document :** 2026-11-01 (horodatage système de la session qui l'a
> produit).
> **Dernière activité de développement constatée (fait vérifié) :** 2026-10-27 20:07:25
> (+01:00), commit `e36cda5`, branche `lot-1-diskpilot`.
> **Auteur de ce document :** instance Claude Code (Sonnet 5), à partir de l'analyse du dépôt
> et du transcript de session local (voir section 0 « Sources consultées »).

---

## Mise à jour du 2026-11-08 (2) — préversion 0.2.1-beta.1 publiée

> Prime sur tout le reste du document.

- **Version** : `0.2.1b1` (PEP 440) / tag `v0.2.1-beta.1`. Le nom `v0.2.0-beta.1` demandé
  aurait été *antérieur* à la `0.2.0` déjà déclarée dans `pyproject.toml` : numéro supérieur
  retenu, conformément à la consigne « sauf si le dépôt comporte déjà […] un numéro plus
  récent ».
- **Ajouté** : exclusions personnalisées DiskPilot (câblées au scan + éditeur dans
  Paramètres) ; distribution (`scripts/package-release.ps1`, `installer/nexusdesk.iss`,
  `CHANGELOG.md`, README utilisateur). Artefacts produits dans `release\<version>\` (ignoré
  par Git) : ZIP portable, installateur par utilisateur, `VERSION.txt`, `SHA256SUMS.txt`.
- **Corrigé** : scan explicite d'un dossier exclu (résultat vide) ; dépréciation Qt
  `AA_UseHighDpiPixmaps`. La suppression reste refusée sous les dossiers protégés.
- **Vérifié** : `check.ps1` vert ; 105 tests réussis + 1 ignoré, couverture 61 % ;
  `smoke-test.ps1` vert ; test UI Automation de l'exe sans Python dans le PATH (volumes,
  scan, doublons, arrêt propre). Mesure réelle : 369 112 fichiers en 66–114 s, ~1,1 Ko de
  mémoire par entrée (détail : `docs/journal-des-lots.md`, « Préversion 0.2.1-beta.1 »).
- **Outils installés sur ce PC** (winget, portée utilisateur) : GitHub CLI 2.103.3,
  Inno Setup 6.7.3 (`%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe`).
- **Publier une version** : `build.ps1` → `smoke-test.ps1` → `package-release.ps1` → tag
  annoté → `gh release create … --prerelease` avec les fichiers de `release\<version>\`.
- **Branche unique (2026-11-08)** : à la demande de l'utilisateur, `lot-1-diskpilot` a été
  fusionnée dans `main` (commit `0e1a642`, avec le fichier `LICENSE` GPL v3 ajouté sur
  GitHub) ; `lot-0-socle` et `lot-1-diskpilot` ont été supprimées (local et GitHub), tous
  leurs commits étant dans `main`. **Développer désormais directement sur `main`.**
- **Incohérence de licence à trancher** : `LICENSE` = GPL v3 (ajouté par l'utilisateur), mais
  `pyproject.toml`, `README.md` et `docs/licences-tierces.md` indiquent « Proprietary ».
- **Prochaines étapes** : licence, décision sur la performance du lot 1, puis lot 2 NetWatch.

## Mise à jour du 2026-11-08 — reprise effective sur le nouvel ordinateur

> Cette section prime sur le reste du document quand ils divergent.

- **Environnement réparé (vérifié)** : le `.venv` copié depuis l'ancien PC était inutilisable
  (interpréteur et installation éditable pointant vers `C:\Users\remid\...`). Il a été
  **déplacé, non supprimé**, vers `..\_sauvegarde-ancien-pc\.venv` (avec une copie de l'ancien
  hook pre-commit), puis `scripts/install-dev.ps1` a recréé l'environnement : Python 3.12.16,
  uv 0.13.6, PySide6 6.12.0, hook pre-commit réinstallé. Le dossier de sauvegarde peut être
  supprimé une fois l'utilisateur d'accord.
- **Sous Windows PowerShell 5.1** (PowerShell 7 absent de ce PC), lancer les scripts via
  `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\<script>.ps1` : rediriger
  leur sortie (`*>&1`) dans la même session fait échouer `$ErrorActionPreference = "Stop"` sur
  le premier message stderr d'un outil natif (uv, pip-audit).
- **État de référence revérifié** : `check.ps1` vert (ruff, mypy, 5 contrats, pip-audit sans
  vulnérabilité) ; `test.ps1 -Integration -Coverage` : 98 réussis, 1 ignoré (symlink, mode
  développeur absent), couverture 58 % — identique à l'ancien PC.
- **Fait** : onglet Paramètres « DiskPilot » (taille minimale des doublons, seuils d'espace
  libre, application sans redémarrage) + **correction d'une anomalie** (tout changement dans
  Général/Apparence réécrivait les réglages DiskPilot par défaut). Détail :
  `docs/journal-des-lots.md`, « Complément post-lot ». Tests : `tests/ui/test_settings_page.py`.
- **Constats nouveaux** : `extra_excluded_paths` (schéma DiskPilot) n'est lu par aucun code
  du scanner ; avertissement de dépréciation `AA_UseHighDpiPixmaps` (`__main__.py:28`) avec
  PySide6 6.12 (attribut sans effet en Qt 6) ; aucun dépôt Git distant configuré.
- **Toujours en attente de décision utilisateur** : performance du lot 1 (accepter l'écart ou
  paralléliser), fusion `lot-1-diskpilot` → `main`, versionnement de ce document.

---

## 0. Sources consultées et limites de cette analyse

Pour respecter l'exigence d'honnêteté du projet lui-même (cahier des charges, section 21),
voici exactement ce qui a été consulté pour produire ce document, et ce qui ne l'a pas été.

**Sources réellement consultées (faits vérifiés) :**
- Le dépôt Git complet : `git log --all`, contenu de tous les fichiers suivis, état de
  l'arbre de travail (propre, aucune modification non commitée au moment de la rédaction).
- Tout `docs/` : `architecture.md`, `dependances.md`, `permissions.md`, `confidentialite.md`,
  `glossaire.md`, `journal-des-lots.md`, `licences-tierces.md`, et les 14 ADR
  (`docs/adr/0001` à `0015`, `0014` n'existe pas — gap numérique volontaire, voir ADR-0015).
- `pyproject.toml`, `uv.lock`, `.pre-commit-config.yaml`, `.python-version`, `.gitignore`,
  `nexusdesk.spec`, tous les scripts PowerShell (`scripts/*.ps1`).
- L'intégralité de l'arborescence `src/nexusdesk/` (91 fichiers Python) et `tests/`
  (46 fichiers de test).
- **Le transcript JSONL local de la session de développement**
  (`C:\Users\remid\.claude\projects\c--Users-remid-Desktop-NexusDesk-NexusDesk---App\fa13f34e-1b73-45aa-9196-7547a8ff0741.jsonl`,
  13,7 Mo, 7357 lignes) — c'est de là qu'a été extrait le **cahier des charges complet**
  (document source de 72 636 caractères, collé par l'utilisateur en tout premier message de
  cette session). Ce fichier contient l'historique brut de la session qui a produit les
  lots 0 et 1 ; il a été utilisé comme source pour ce document, mais **n'a pas été relu
  ligne à ligne dans son intégralité** (7357 lignes, coût prohibitif) — seuls le cahier des
  charges et les faits déjà résumés dans le contexte de conversation ont été exploités.
- Le répertoire mémoire Claude Code propre à ce projet
  (`...\memory\`) : **vide**, aucune mémoire n'y a encore été enregistrée.
- `.claude/settings.local.json` : configuration locale, ne contient pas d'information
  pertinente pour la reprise (permissions d'outils, propre à la machine actuelle).

**Ce qui n'a PAS été consulté ou n'existe pas :**
- Aucune conversation Claude Code antérieure à celle contenue dans ce transcript unique n'a
  été trouvée. Il n'y a pas d'historique Claude Code multi-sessions pour ce projet : tout le
  développement (lots 0 et 1) a eu lieu dans une seule session continue (le fichier
  `.jsonl` ci-dessus), étalée sur deux jours (2026-10-25 puis 2026-10-27).
- Aucun fichier `CLAUDE.md` n'existe à la racine du projet (vérifié : absent du dépôt et du
  répertoire de travail). Le seul fichier `.claude/` présent est `settings.local.json`.
- Le cahier des charges tel que cité par `README.md` (« se trouve dans `reports/`, hors
  dépôt ») n'était **pas présent sous cette forme** au moment de la première rédaction de ce
  document : `reports/` ne contenait que le plan de lot 1 (`spicy-giggling-taco.md`, un plan
  de travail généré en mode plan, pas le cahier des charges complet) — et ce dossier est de
  toute façon exclu de Git (`.gitignore`), donc impropre à y stocker un document destiné à
  survivre au transfert. **Correction apportée après la première rédaction** : l'utilisateur
  a fourni directement le texte intégral et propre (sans corruption d'encodage, contrairement
  à l'extraction faite depuis le transcript JSONL) du cahier des charges v2, qui a été
  enregistré tel quel dans **`docs/cahier-des-charges-v2.md`** (suivi par Git, comme les
  autres documents de référence du projet). **Ce fichier est désormais la source canonique à
  lire en priorité** sur le nouvel ordinateur — il n'y a plus besoin du transcript de session
  pour y accéder, et il sera transféré automatiquement par un simple `git clone`/`git pull`.
- Aucune recherche exhaustive du disque entier n'a été menée pour trouver d'autres copies du
  cahier des charges (une recherche large a été lancée puis interrompue car improductive).
- Non déterminé : si l'utilisateur dispose d'une copie du cahier des charges ailleurs
  (document Word, Notion, etc.), ce document n'en a pas eu connaissance.

**Mise à jour post-rédaction :** le point ci-dessus est résolu. L'utilisateur a transmis le
texte intégral et propre du cahier des charges v2 directement dans la conversation ; il a
été enregistré sans modification de contenu dans `docs/cahier-des-charges-v2.md` (et non
dans `reports/`, qui est ignoré par Git — voir la remarque de la section précédente). Ce
nouveau fichier documentaire (pas un fichier applicatif du code de NexusDesk) a été ajouté
au dépôt à la demande implicite de l'utilisateur, qui en a fourni le contenu pour cet usage
précis. Il ne remplace ni ne modifie aucun fichier existant. **Il n'a pas encore été commité
dans Git** (aucun `git add`/`git commit` n'a été exécuté) — l'utilisateur doit valider ce
commit lui-même, conformément à la consigne de ne pas agir sur l'état partagé du dépôt sans
confirmation explicite.

---

## 1. Présentation du projet

### 1.1 Identité

**Nom :** NexusDesk
**Nature :** boîte à outils Windows 11 locale, gratuite et sans télémétrie.
**Version actuelle :** 0.2.0 (`pyproject.toml`), correspondant à la fin du lot 1.
**Licence :** `Proprietary` (champ `license` de `pyproject.toml`) — à noter, ce champ est
peut-être provisoire : le cahier des charges (section 18, « Signature de code ») évoque une
publication open source possible comme question ouverte (section 22), jamais tranchée.

### 1.2 Mission et principes (cahier des charges, section 1)

NexusDesk vise à être l'outil qu'on ouvre chaque jour pour comprendre et entretenir son PC,
sans compte, sans abonnement et sans envoi de données. Sept principes non négociables
gouvernent toutes les décisions techniques :

1. **Local d'abord** : aucune donnée ne quitte le PC, sauf requête explicite (mise à jour
   winget, téléchargement d'un modèle OCR, test réseau vers une cible choisie).
2. **Honnêteté des données** : aucune valeur inventée ; une collecte qui échoue s'affiche
   comme indisponible, avec la raison.
3. **Faits séparés des hypothèses** : toute interprétation (doublon probable, cause de
   coupure réseau) est présentée comme telle, jamais comme un fait.
4. **Rien d'irréversible sans confirmation** : suppressions vers la Corbeille par défaut,
   aperçu de la commande avant exécution.
5. **Moindre privilège** : l'interface ne tourne jamais en administrateur ; l'élévation
   passe par un assistant dédié, à la demande, avec explication.
6. **Interface jamais figée** : toute opération de plus de 100 ms s'exécute en tâche de
   fond, annulable.
7. **Aucun bouton factice** : une fonction non terminée est absente de l'interface, jamais
   grisée sans raison.

Ces principes **sont le fil conducteur de toutes les décisions déjà prises** dans le code
(voir par exemple `ui/components/placeholder_page.py`, qui matérialise le principe 7 : un
module non commencé affiche honnêtement « Module à venir — Lot N » plutôt qu'une page
vide ou des contrôles inertes).

### 1.3 Les six modules visés (périmètre v1.0)

| Module | Rôle | Lot cible | Version cible | État réel (voir section 3) |
| --- | --- | --- | --- | --- |
| **AppManager** | Inventaire logiciels (registre + WinGet), installation/désinstallation/mises à jour, gestion du démarrage | 7 | 0.8 | Non commencé (stub) |
| **NetWatch** | Surveillance réseau continue, détection et localisation des coupures, graphiques, diagnostic guidé | 2 | 0.3 | Non commencé (stub) |
| **ScreenText** | Capture d'écran + OCR (Windows OCR / Tesseract), historique chiffré | 5 | 0.6 | Non commencé (stub) |
| **LogDoctor** | Lecture des journaux Windows, regroupement, corrélation temporelle, fiches de diagnostic | 6 | 0.7 | Non commencé (stub) |
| **DiskPilot** | Analyse d'espace disque (treemap), doublons, suppression vers la Corbeille | 1 | 0.2 | **Terminé avec réserve** (voir 3.2) |
| **ClipVault** | Historique chiffré du presse-papiers, exclusions, modèles | 4 | 0.5 | Non commencé (stub) |

Autour de ces modules : un **tableau de bord** (lot 3, v0.4), une **recherche globale FTS5**
et une **palette de commandes Ctrl+K** (même lot), et un **socle technique** (lot 0, v0.1,
terminé) qui porte l'architecture, la base de données, le design system et le shell.

### 1.4 Plan de livraison par lots (cahier des charges, section 19)

Le projet avance en **9 lots** (0 à 8), chacun produisant une version installable et
utilisable. Durée totale estimée par le cahier des charges : 19 à 24 semaines à temps plein
pour un développeur expérimenté — à relativiser : les lots 0 et 1 ont en pratique été
réalisés en deux sessions de travail (2026-10-25 et 2026-10-27), avec un agent IA, pas un
développeur humain à temps plein ; cette estimation de durée n'est donc pas directement
transposable à la suite du projet avec Claude Code.

| Lot | Version | Contenu | Critère de sortie | État |
| --- | --- | --- | --- | --- |
| 0. Socle | 0.1 | uv, structure, config, bases + Alembic, gestionnaire de tâches, journalisation, instance unique, tray, fenêtre/navigation, design system, paramètres de base, diagnostic d'installation, scripts | Exécutable empaqueté démarre/réduit/rouvre ; migrations et sauvegardes testées | ✅ Terminé et vérifié |
| 1. DiskPilot | 0.2 | Volumes, scan, treemap, doublons, suppression Corbeille, export | Scan d'1M fichiers sans gel, tests liens/cloud verts | ⚠️ Terminé avec réserve (critère de performance non garanti, voir 3.2) |
| 2. NetWatch | 0.3 | Interfaces, sondes, coupures, graphiques, diagnostic guidé, tests de ports, découverte locale | 24h de surveillance sans fuite mémoire, classification des coupures testée | ⬜ Non commencé |
| 3. Tableau de bord et recherche | 0.4 | Cartes, bandeau santé, palette de commandes, recherche FTS5 | Toutes les cartes alimentées par des données réelles ou « Indisponible » | ⬜ Non commencé |
| 4. ClipVault | 0.5 | Écoute, exclusions, chiffrement, fenêtre rapide, modèles, transformations, rétention | Tests de formats d'exclusion et d'absence de contenu dans les journaux verts | ⬜ Non commencé |
| 5. ScreenText | 0.6 | Capture multi-écran, Windows OCR, Tesseract, résultat, historique, QR codes | Taux de caractères corrects ≥ 95 % sur jeu d'images de référence | ⬜ Non commencé |
| 6. LogDoctor | 0.7 | Collecte, regroupement, chronologie, contexte, 40 fiches, exports | Fiches relues, faits/hypothèses séparés dans toutes les vues | ⬜ Non commencé |
| 7. AppManager + assistant élevé | 0.8 | Inventaire, WinGet, file d'opérations, démarrage, export liste ; assistant élevé | Installation/mise à jour/désinstallation testées sur Windows Sandbox | ⬜ Non commencé |
| 8. Finitions | 0.9–1.0 | Accessibilité, performance, onboarding, installateur, mises à jour, documentation, rapport de validation | Tous les critères de la section 20 remplis | ⬜ Non commencé |

**Règle du cahier des charges (section 21.2), scrupuleusement suivie jusqu'ici** : un lot à
la fois par session, pas de lot suivant sans avoir rempli (ou honnêtement documenté l'écart
au) critère de sortie du lot en cours.

---

## 2. Architecture technique

### 2.1 Stack retenue (cahier des charges, section 3 — état réel du code en regard)

| Couche | Choix du cahier des charges | État dans le code au lot 1 |
| --- | --- | --- |
| Langage | Python 3.12 | ✅ `requires-python = ">=3.12,<3.13"` |
| Environnement | uv + `uv.lock` | ✅ |
| Interface | PySide6 6.8+ (Qt Widgets) | ✅ `pyside6>=6.8,<7` |
| Graphiques | pyqtgraph | ⬜ Pas encore ajouté (prévu lot 2/3, courbes réseau et tableau de bord) |
| Base de données | SQLite (WAL, FTS5) | ✅ WAL ; **FTS5 non câblé** (prévu lot 3, recherche globale) |
| ORM | SQLAlchemy 2.0 typé | ✅ |
| Migrations | Alembic | ✅ |
| Configuration | pydantic v2 + pydantic-settings | ✅ pydantic ; `pydantic-settings` listé en dépendance mais **pas encore utilisé dans le code** (à vérifier au prochain lot qui en a besoin) |
| Système | psutil | ✅ ajouté au lot 1 |
| API Windows | pywin32 + ctypes | ✅ |
| WinRT | pywinrt | ⬜ Pas encore ajouté (nécessaire pour Windows OCR, lot 5) |
| OCR | Tesseract en sous-processus | ⬜ Pas encore utilisé (lot 5) |
| DNS | dnspython | ⬜ Pas encore ajouté (lot 2) |
| Tests | pytest, pytest-qt, pytest-cov, hypothesis | ✅ (hypothesis listé mais pas encore utilisé pour des tests de propriétés réels) |
| Qualité | Ruff, mypy --strict, pre-commit | ✅ |
| Packaging | PyInstaller (mode dossier) + Inno Setup | ✅ PyInstaller ; ⬜ Inno Setup pas encore fait (lot 8) |
| Icônes | Fluent UI System Icons (SVG) | À vérifier concrètement dans `src/nexusdesk/resources/icons/` au prochain lot qui en ajoute |

### 2.2 Processus et instance unique

Un seul processus résident `NexusDesk.exe` (utilisateur standard), avec :
- icône de zone de notification (tray) ;
- fenêtre principale créée au démarrage ;
- instance unique via mutex nommé `Local\NexusDesk` (`integrations/windows/single_instance.py`,
  ADR-0002) ;
- un second lancement transmet sa demande (`OPEN_MAIN_WINDOW` ou `QUIT`) via un tube nommé
  `\\.\pipe\NexusDesk` (ACL restreinte au SID de l'utilisateur courant) puis se termine
  rapidement, **sans jamais créer de `QApplication`**.

L'**assistant élevé** `NexusDesk.Elevated.exe` (pour les opérations exigeant `HKLM`, le
journal Security Windows, une désinstallation machine) **n'existe pas encore** — prévu lot 7
(ADR-0001). L'architecture actuelle ne fait rien qui en empêcherait l'ajout sans refonte (le
canal IPC du lot 0 suit déjà le même modèle prévu pour lui).

### 2.3 Couches et règles de dépendance

```
ui/            → viewmodels/, core/           (jamais integrations/, database/)
viewmodels/    → services/, core/             (jamais ui/, integrations/)
services/      → repositories/, core/         (jamais Qt, ui/, integrations/)
repositories/, database/ → models/, core/     (jamais services/, ui/)
integrations/  → core/                        (jamais services/, ui/)
```

Ces règles sont **vérifiées automatiquement** par `import-linter` (5 contrats dans
`pyproject.toml`, `[[tool.importlinter.contracts]]`), avec `allow_indirect_imports = true` :
l'interdiction porte sur les imports **directs** entre couches non autorisées, pas sur la
dépendance transitive normale (ex. `ui` dépend bien de `database` au bout du compte, mais
uniquement via `viewmodels → services → repositories`).

`app.py` est la **racine de composition** : seul module autorisé à importer toutes les
couches pour les assembler (`Application.__init__`). Il n'est soumis à aucun contrat
import-linter.

### 2.4 Arborescence réelle du code (`src/nexusdesk/`)

```
src/nexusdesk/
  __init__.py, __main__.py          point d'entrée : instance unique puis boucle Qt
  app.py                            racine de composition (Application.__init__)
  core/                             tâches (TaskManager/QThreadPool), erreurs typées,
                                     chemins (mode portable), journalisation (rotation,
                                     rédaction du profil utilisateur), diagnostics
  config/                           schémas pydantic des paramètres (schema.py)
  database/                        moteur SQLite (PRAGMA), sessions, file d'écriture
                                     unique (write_queue.py), sauvegarde/restauration,
                                     exécuteur de migrations (migration_runner.py)
    migrations/versions/            0001_initial.py (table settings), 0002_diskpilot.py
                                     (7 tables DiskPilot)
  models/                           entités SQLAlchemy (base.py, settings.py,
                                     diskpilot.py, diskpilot_cache.py) + dataclasses
                                     pures de domaine (diskpilot_domain.py)
  repositories/                     settings_repository.py + 3 dépôts DiskPilot
  services/
    diskpilot/                     scanner, categorizer, exclusions, duplicate_finder,
                                     deletion_service, cleanup_suggestions,
                                     comparison_service, export_service,
                                     volumes_service, ports.py (Protocols)
    (appmanager/, netwatch/, screentext/, logdoctor/, clipvault/, search/, dashboard/
     prévus par le cahier des charges — AUCUN de ces sous-paquets n'existe encore)
  integrations/
    windows/                       single_instance, tray, notifications, mica, startup,
                                     filesystem (DiskPilot)
    (winget/, network/, ocr/, clipboard/, eventlog/, storage/ prévus — n'existent pas)
  elevated/                         prévu — n'existe pas
  viewmodels/                       diagnostics, settings, shell + 7 viewmodels DiskPilot
  ui/
    shell/                          main_window.py, navigation.py
    pages/                          une page par module (stubs PlaceholderPage pour les
                                     5 non commencés) + diskpilot/ (sous-paquet complet,
                                     6 panneaux + treemap + dialogue de suppression)
    components/                    placeholder_page, gauge_bar, formatting
    theme/                         tokens, qss_builder, theme_manager, icon_provider
  resources/, knowledge/             prévus (icônes SVG, fiches YAML LogDoctor) — à
                                     vérifier s'ils contiennent déjà des fichiers
tests/   unit/ (46 fichiers), integration/, ui/, fixtures/
docs/    architecture, dépendances, permissions, confidentialité, glossaire,
         journal-des-lots, licences-tierces, adr/ (14 fichiers)
scripts/ install-dev.ps1, run.ps1, test.ps1, check.ps1, build.ps1, smoke-test.ps1
```

**Point important pour la suite :** `services/`, `integrations/windows/` et `ui/pages/`
n'ont, pour l'instant, que le contenu DiskPilot (lot 1) en plus du socle. Les 5 autres
modules sont des pages `PlaceholderPage` vides — c'est **honnête et volontaire** (principe 7
du cahier des charges), pas un oubli.

### 2.5 Base de données

Deux fichiers SQLite sous `%LOCALAPPDATA%\NexusDesk\data\` :
- `nexusdesk.db` — paramètres (table clé/valeur à plat, ADR-0003) + toutes les tables
  DiskPilot (7 tables, migration `0002_diskpilot`). Mode WAL, `foreign_keys=ON`,
  `busy_timeout=5000`, `synchronous=NORMAL` sur chaque connexion (`database/engine.py`).
- `metrics.db` — créée et configurée dès le lot 0 (PRAGMA appliqués) mais **sans schéma
  Alembic encore** (ADR-0008) : en attente du lot 2 (NetWatch), qui y écrira les mesures
  réseau brutes.

Une **troisième base séparée**, `diskpilot_hash_cache.db` (sous `cache\`, ADR-0015), stocke
le cache d'empreintes de déduplication — **hors chaîne Alembic principale** (donnée dérivée,
jetable), avec sa propre file d'écriture.

Toute écriture métier passe par une **file d'écriture unique** par base
(`database/write_queue.py`, ADR-0007 : un `threading.Thread` démon + `queue.Queue`), pour
éviter les verrous SQLite entre fils de travail.

**Migrations** : Alembic invoqué programmatiquement au démarrage
(`database/migration_runner.py`). Si une migration est nécessaire : sauvegarde via l'API
`backup` de SQLite + `PRAGMA integrity_check` avant tentative ; en cas d'échec, restauration
automatique et démarrage en lecture seule (jamais de perte de données) — **ce mécanisme est
testé réellement** (`tests/integration/database/test_migration_failure_restore.py`), pas
seulement écrit.

### 2.6 Gestionnaire de tâches (`core/tasks.py`)

`TaskManager` encapsule une instance dédiée de `QThreadPool`. Chaque tâche :
- a une **clé de déduplication** (deux tâches identiques ne peuvent pas tourner en même
  temps — `TaskManager.submit` renvoie `None` si une tâche avec la même clé est déjà en
  cours) ;
- reçoit un `CancellationToken` (coopératif, vérifié par la tâche elle-même dans ses
  boucles) et un `ProgressReporter` (débit borné à ~10 mises à jour/s) ;
- ne laisse **jamais** une exception s'échapper de `QRunnable.run()` (piège connu de Qt :
  une exception y est silencieusement perdue sinon) — toute erreur est capturée et republiée
  via le signal `failed`, typée (`DependencyMissing`, `PermissionDenied`, `Timeout`,
  `Cancelled`, `core/errors.py`) quand elle en provient, sinon l'exception d'origine.

### 2.7 Design system

Jetons uniques (`ui/theme/tokens.py`) → génération QSS par assemblage Python natif
(`ui/theme/qss_builder.py`, ADR-0004, pas de Jinja2) → application par `ThemeManager`
(thème sombre/clair/« suivre Windows », effet Mica avec repli silencieux si indisponible).
Icônes SVG chargées via `QSvgRenderer` + composition `SourceIn` (pas `QIcon(chemin)`, pour
éviter une dépendance au plugin Qt `iconengines` dans l'exécutable packagé).

Lot 1 y a ajouté `CATEGORY_COLORS` (couleurs par catégorie de fichier pour le treemap
DiskPilot) et deux composants réutilisables : `gauge_bar.py` (jauge colorée) et
`formatting.py` (formatage d'octets lisibles).

### 2.8 Permissions et sécurité (état réel, lots 0+1)

Aucune fonction livrée à ce jour n'exige l'administrateur. Détail dans
`docs/permissions.md` — résumé :

| Opération | Mécanisme | Lot |
| --- | --- | --- |
| Mutex nommé, tube nommé | DACL restreinte au SID utilisateur | 0 |
| Lecture/écriture `%LOCALAPPDATA%\NexusDesk` | Dossier utilisateur | 0 |
| Clé `HKCU\...\Run` | Ruche utilisateur, pas `HKLM` | 0 |
| Effet Mica | API DWM, utilisateur standard | 0 |
| Liste des volumes | `psutil`, `win32api.GetVolumeInformation` | 1 |
| Scan de dossier | `os.scandir`/`os.stat`, utilisateur standard | 1 |
| Envoi à la Corbeille | `SHFileOperation` + `FOF_ALLOWUNDO` (ADR-0010) | 1 |
| Suppression définitive | **Jamais câblée** (réglage existe, décoché) | 1 |

### 2.9 Confidentialité (état réel, lots 0+1)

Aucun appel réseau sortant à ce jour. Journaux techniques : chemin du profil utilisateur
systématiquement remplacé par `%USERPROFILE%` (`core/logging_setup.py`, filtre de
formatage). Les fichiers OneDrive à la demande ne sont jamais ouverts ni lus. Détail complet
dans `docs/confidentialite.md`.

---

## 3. État réel détaillé par fonctionnalité

> Rappel de la consigne appliquée ici : le code existant ne suffit pas à qualifier une
> fonctionnalité de « terminée ». Chaque ligne ci-dessous distingue ce qui est **vérifié par
> test ou exécution réelle** de ce qui est seulement écrit.

### 3.1 Socle technique (Lot 0 — v0.1) — ✅ Terminé et vérifié

| Élément | État | Preuve |
| --- | --- | --- |
| Squelette projet, `pyproject.toml`, `uv.lock`, Python 3.12 épinglé | ✅ Fait | Fichiers présents, `uv sync` fonctionnel (vérifié à nouveau pendant le lot 1) |
| Ruff, mypy --strict, import-linter, pre-commit | ✅ Fait et vérifié | `scripts/check.ps1` vert à la fin du lot 1 |
| `pip-audit` | ✅ Fait et vérifié | Aucune vulnérabilité connue au lot 1 ; une CVE pytest corrigée au lot 0 (voir section 6) |
| Bases SQLite + Alembic (révision initiale) | ✅ Fait et vérifié | `tests/integration/database/` |
| Sauvegarde/intégrité/restauration | ✅ Fait et vérifié **par test réel** | Échec de migration simulé → sauvegarde prise, restauration exacte, bascule lecture seule : testé explicitement |
| Gestionnaire de tâches | ✅ Fait et vérifié | `tests/unit/core/test_tasks.py` |
| Instance unique (mutex + tube nommé) | ✅ Fait et vérifié avec **deux vrais processus séparés** | `tests/integration/windows/test_single_instance.py` |
| Design system, shell, navigation Ctrl+1 à Ctrl+7 | ✅ Fait | `tests/ui/test_main_window.py` |
| Pages Paramètres (Général/Apparence) et Diagnostic | ✅ Fait | Fonctionnelles, testées |
| Exécutable packagé (PyInstaller, mode dossier) | ✅ Fait et vérifié | 133,1 Mo (< objectif 150 Mo), séquence démarrage→réduction→réouverture→fermeture vérifiée manuellement ET par `scripts/smoke-test.ps1` |
| Navigation clavier complète, Narrateur Windows | ⚠️ **Non vérifié** | Raccourcis fonctionnels, mais aucun test avec le Narrateur Windows (reporté, critère plutôt de fin de projet — section 20) |
| Mise à l'échelle DPI mixte, multi-écran | ⚠️ **Non vérifié** | Nécessite plusieurs écrans physiques, indisponible pendant la session |
| Effet Mica (rendu visuel réel) | ⚠️ **Non vérifié à l'œil** | Le code applique l'attribut DWM sans lever d'exception, mais la translucidité réelle n'a jamais été confirmée visuellement (aucune capture d'écran prise) |
| Onglet « À propos », installateur Inno Setup, assistant élevé | ⬜ Non fait | Prévus lots 7/8 |

### 3.2 DiskPilot (Lot 1 — v0.2) — ⚠️ Terminé avec réserve

**Fonctionnalités terminées et vérifiées :**

| Fonction | Fichiers principaux | État |
| --- | --- | --- |
| Liste des volumes (lettre, libellé, FS, type, jauge) | `integrations/windows/filesystem.py::list_volumes`, `viewmodels/diskpilot_volumes_viewmodel.py`, `ui/pages/diskpilot/volumes_panel.py` | ✅ Testé contre de vrais volumes (`tests/integration/windows/test_filesystem_volumes.py`) |
| Scan récursif (pile explicite, jamais `os.walk`) | `services/diskpilot/scanner.py` | ✅ Testé avec liens physiques réels, jonctions réelles (`mklink /J`), dossiers exclus réels |
| Taille logique vs taille sur disque (compression/fichiers creux) | `scanner.py::size_on_disk_may_differ_from_logical_size` | ✅ Appel Win32 coûteux seulement si nécessaire (optimisation du lot 1, voir section 6) |
| Liens physiques comptés une seule fois | `scanner.py` (`st_nlink > 1` → `get_hardlink_key`) | ✅ Testé avec un vrai hardlink (`os.link`) |
| Jonctions/symlinks jamais suivis, enregistrés à part | `scanner.py::_handle_directory` | ✅ Testé (jonction réelle `mklink /J` ; symlink testé mais `skipif` si droits insuffisants) |
| Fichiers OneDrive à la demande jamais lus | `scanner.py::is_onedrive_placeholder` (masque de bits) | ⚠️ Logique pure testée ; **jamais testée avec un vrai client OneDrive** (impossible de simuler l'attribut réel, voir section 6) |
| Exclusions par défaut (dossiers système) | `services/diskpilot/exclusions.py` | ✅ Testé, y compris exemption de la racine choisie |
| Treemap squarifié (algorithme Bruls/Huizing/van Wijk) | `ui/pages/diskpilot/treemap_widget.py` | ✅ Conservation d'aire, absence de recouvrement, navigation par double-clic — tous testés |
| Détection de doublons (taille → empreinte partielle → complète, cache) | `services/diskpilot/duplicate_finder.py` | ✅ Testé avec fichiers réels, cache vérifié |
| Suppression vers la Corbeille (revérification, refus système/verrouillé) | `services/diskpilot/deletion_service.py` | ✅ Testé avec un fichier réellement envoyé et retiré de son dossier (`tests/integration/windows/test_recycle_bin.py`) |
| Suppression **définitive** | — | ⬜ Jamais câblée (réglage existe, décoché par défaut) |
| Suggestions de nettoyage (installateurs anciens, TEMP, doublons, gros fichiers) | `services/diskpilot/cleanup_suggestions.py` | ✅ Testé |
| Rétention (5 derniers scans/dossier, cascade FK) | `repositories/diskpilot_scan_repository.py` | ✅ Testé par insertion réelle de 7 scans puis vérification |
| Export CSV (fichiers, dossiers, doublons) | `services/diskpilot/export_service.py` | ✅ Testé |
| Comparaison entre deux scans | `services/diskpilot/comparison_service.py`, `ui/pages/diskpilot/history_panel.py` | ✅ Testé (sur l'échantillon des 1000 plus gros fichiers persistés, pas l'arbre complet) |
| Interface complète (6 panneaux), câblage dans `app.py` | `ui/pages/diskpilot/*`, `app.py` | ✅ L'application démarre réellement, la page se construit sans exception |

**Réserve majeure — critère de performance non garanti :**

Le critère de sortie du lot (scan d'1 million de fichiers en moins de 3 minutes / 180 s sur
SSD NVMe) **n'est pas garanti de façon reproductible**, malgré une vraie amélioration de 2 à
2,8× obtenue pendant la validation. Détail complet en section 6.1 et dans
`docs/journal-des-lots.md` / `docs/adr/0011-...md`. En résumé :

| Étape | Temps mesuré (1M fichiers réels) |
| --- | --- |
| Avant correctifs | 697,6 s |
| Après correction du bug `is_excluded` | 362,1 s |
| + désactivation du GC (isolé) | 246,3 s |
| Tous les correctifs combinés (code livré) | 341,1 s |

La cause la plus plausible de l'écart restant (341 s > 180 s) est la protection temps réel
de Windows Defender (confirmée active, sans exclusion configurée), un facteur hors du
contrôle de l'application. **Non fait** : parallélisation du parcours (piste identifiée,
non explorée).

**Terminé non vérifié (manuellement) :**
- Interaction manuelle complète de chaque panneau (clics, sélection, suppression réelle
  depuis l'interface) — aucun outil d'automatisation d'interface disponible pendant la
  session, seule la construction de la page a été vérifiée (démarrage réel sans exception).

**Non fait :** *(point ci-dessous réalisé le 2026-11-08, voir la section de mise à jour en tête)*
- Exposition du réglage `min_duplicate_size_bytes` dans la page Paramètres (la valeur existe
  en base, lue au démarrage, mais aucun contrôle d'interface ne permet encore de la
  modifier — seuls les onglets Général/Apparence existent dans `SettingsPage`).

### 3.3 Les 5 autres modules — ⬜ Non commencés

AppManager, NetWatch, ScreenText, LogDoctor, ClipVault n'ont, à ce jour, **aucun code
métier** : chaque page est une `PlaceholderPage` (`ui/components/placeholder_page.py`)
affichant honnêtement « Module à venir — Lot N ». Aucun fichier dans `services/`,
`integrations/windows/` (hormis ceux de DiskPilot) ni `repositories/` ne les concerne.
`config/schema.py` ne contient que `GeneralSettings`, `AppearanceSettings` et
`DiskPilotSettings` — pas de modèle pour les 5 autres modules encore.

### 3.4 Tableau de bord, recherche globale, palette de commandes — ⬜ Non commencés

`DashboardPage` est un stub (`PlaceholderPage("Tableau de bord", "Lot 3")`). Aucune carte,
aucun FTS5, aucune palette Ctrl+K dans le code à ce jour.

---

## 4. Point exact où le développement s'est arrêté

**Date et heure (fait vérifié, horodatage du dernier commit Git) :** 2026-10-27 20:07:25
+01:00.
**Commit :** `e36cda5` — « Clore le lot 1 : passer en v0.2.0, journal des lots avec compte
rendu honnête de performance ».
**Branche :** `lot-1-diskpilot` (créée depuis `main`, qui pointe toujours sur la fin du
lot 0 — `8b18485` — **`lot-1-diskpilot` n'est PAS encore fusionnée dans `main`**).
**Arbre de travail :** propre, aucune modification non commitée (vérifié par `git status`
au moment de la rédaction de ce document).

### 4.1 Dernière tâche demandée

D'après le transcript de session, la dernière instruction de développement de l'utilisateur
dans cette session a été **« continue le projet »** (une instruction unique, répétée
implicitement pour poursuivre le travail en cours), interprétée comme : poursuivre le lot 1
(DiskPilot) selon le plan déjà validé en mode plan (`reports/spicy-giggling-taco.md`), avec
la méthodologie imposée par le cahier des charges (section 21).

**Après la clôture du lot 1** (commit `e36cda5`), l'utilisateur a enchaîné avec deux demandes
distinctes, toutes deux sans rapport avec le développement du produit lui-même :
1. `/graphify` (commande slash) — tentative de construction d'un graphe de connaissances du
   projet. **Résultat : bloquée.** L'outil `graphify` déjà installé sur cette machine
   (`~/.local/bin/graphify`, v0.8.30) est une version native différente de celle attendue par
   le skill (qui suppose un paquet Python importable `graphifyy`) ; son installation a été
   refusée par le classificateur de permissions (nom de paquet jugé non vérifié), et la
   commande `graphify extract .` déjà installée a refusé de fonctionner sans clé API LLM
   (`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, etc. — aucune n'est définie sur cette machine).
   **Aucun graphe n'a donc été produit.** Cette tentative n'a rien modifié dans le dépôt.
2. La présente demande : produire ce document `PROJECT_HANDOVER.md`.

### 4.2 Ce qui a été fait pendant le lot 1 (résumé exécutif, détails en section 3.2 et 6)

Dans l'ordre chronologique réel (d'après les horodatages des commits) :
1. 13:04–13:31 — modèles SQLAlchemy, migration `0002_diskpilot`, intégrations Windows
   (`filesystem.py`), services métier, dépôts, réglages, viewmodels.
2. 20:03 — construction du sous-paquet `ui/pages/diskpilot/` (6 panneaux + treemap) et
   câblage complet dans `app.py`.
3. 20:04 — **découverte et correction d'un bug réel de performance** dans `is_excluded`
   pendant la validation à grande échelle (voir section 6.1) ; ajout des tests unitaires et
   d'intégration.
4. 20:05 — rédaction des 5 ADR du lot (0010 à 0015, sans 0014), mise à jour de toute la
   documentation (`architecture.md`, `dependances.md`, `permissions.md`, `confidentialite.md`,
   `glossaire.md`, `licences-tierces.md`).
5. 20:07 — version 0.2.0, finalisation de `docs/journal-des-lots.md` avec le compte rendu
   honnête de performance, commit de clôture.

### 4.3 Fichiers modifiés durant le lot 1 (liste complète, d'après les commits)

**Créés :**
`src/nexusdesk/models/diskpilot.py`, `diskpilot_cache.py`, `diskpilot_domain.py` ;
`src/nexusdesk/database/migrations/versions/0002_diskpilot.py` ;
`src/nexusdesk/integrations/windows/filesystem.py` ;
`src/nexusdesk/services/diskpilot/` (10 fichiers) ;
`src/nexusdesk/repositories/diskpilot_*.py` (3 fichiers) ;
`src/nexusdesk/viewmodels/diskpilot_*.py` (7 fichiers) ;
`src/nexusdesk/ui/components/gauge_bar.py`, `formatting.py` ;
`src/nexusdesk/ui/pages/diskpilot/` (10 fichiers) ;
`docs/adr/0010` à `0013`, `0015` ;
46 fichiers de test (`tests/unit/services/diskpilot/`, `tests/unit/repositories/`,
`tests/unit/ui/test_diskpilot_treemap_layout.py`, `tests/integration/windows/test_filesystem_volumes.py`,
`test_recycle_bin.py`, `test_scan_performance_canary.py`, `tests/ui/test_diskpilot_treemap.py`).

**Modifiés :** `app.py`, `pyproject.toml` (ajout `psutil`, version → 0.2.0), `uv.lock`, tous
les fichiers `docs/*.md` (hors ADR 0001-0009), `src/nexusdesk/ui/theme/tokens.py`.

**Supprimé :** `src/nexusdesk/ui/pages/diskpilot_page.py` (ancien stub plat, remplacé par le
sous-paquet).

### 4.4 Commandes exécutées pendant la session (catégories, pas l'historique shell exact)

- `uv sync`, `uv run pytest ...` (très nombreuses fois, par fichier puis suite complète),
  `uv run ruff check/format`, `uv run mypy src`, `uv run lint-imports`, `uv run pip-audit`,
  `uv run pip-licenses`.
- `scripts/check.ps1` et `scripts/test.ps1 -Integration -Coverage` (exécutés en fin de lot,
  **tous deux verts** au commit final).
- Scripts Python ad hoc dans le répertoire temporaire (génération de 1 000 000 de fichiers
  réels pour la validation de performance, micro-benchmarks isolés) — **tous nettoyés** en
  fin de session (`rm -rf` du dossier de test de performance confirmé exécuté).
- `git add` / `git commit` (10 commits distincts pour le lot 1, voir `git log`).

### 4.5 Erreurs rencontrées et résolues pendant cette session

Voir section 6 pour le détail technique complet. Liste : vulnérabilité pytest (lot 0,
corrigée) ; bug de performance `is_excluded` (lot 1, corrigé) ; échecs de commit pre-commit
dus au hook mypy qui type-check tout `src/` indépendamment des fichiers stagés (contournés en
adaptant l'ordre des commits, pas un bug du code) ; échec du canari de performance
automatisé dû à l'interférence de Windows Defender (seuil abaissé en conséquence).

### 4.6 Décisions en attente / non tranchées

D'après le cahier des charges (section 22, « Questions ouvertes »), rien n'a été tranché
pendant cette session sur :
- Publier le projet en open source (conditionne signature de code gratuite et publication
  WinGet, à trancher avant le lot 8).
- Liste définitive des cibles Internet par défaut pour NetWatch (à trancher au lot 2).
- Option d'images dans ClipVault en v1.1 (après la v1.0, hors périmètre actuel).
- Support Windows 10 : simple tolérance ou support testé (à trancher au lot 8).
- Raccourcis clavier par défaut à confirmer après essai sur le poste cible (lot 4).

**Décision technique en attente, propre au lot 1 :** la parallélisation du scan DiskPilot
(piste identifiée pour fiabiliser le critère des 180 s) n'a pas été explorée ni décidée.

### 4.7 Ce qui était prévu ensuite, d'après le cahier des charges

Le lot suivant logique est le **lot 2 — NetWatch** (v0.3). Rien n'a été commencé sur ce lot
pendant cette session (aucun fichier `services/netwatch/`, `integrations/windows/network/`
ni `integrations/network/` n'existe).

---

## 5. Prochaines étapes — feuille de route priorisée

### 5.1 Reprise immédiate du développement

1. **Fusionner `lot-1-diskpilot` dans `main`.**
   - Fichiers concernés : aucun changement de code, seulement l'historique Git.
   - Prérequis : vérifier que `main` n'a pas évolué indépendamment (peu probable, mais à
     confirmer par `git log main` sur le nouvel ordinateur).
   - Risque : faible (fast-forward probable, `main` est un ancêtre direct de
     `lot-1-diskpilot`).
   - Critère de réussite : `git log main --oneline -1` montre `e36cda5` après la fusion.
   - **Ceci n'a pas été fait pendant cette session** — à faire consciemment, avec l'accord
     de l'utilisateur (action Git qui modifie l'état partagé du dépôt).

2. **Relire ce document (`PROJECT_HANDOVER.md`) et le cahier des charges complet**
   (`docs/cahier-des-charges-v2.md`, désormais suivi par Git — voir section 0).

### 5.2 Corrections bloquantes

Aucune correction bloquante au sens strict : le lot 1 est fonctionnellement complet et tous
les tests automatisés passent. La seule réserve sérieuse est la performance (section 3.2),
qui **ne bloque pas l'usage** (un scan de 1M fichiers prend ~3,8 à 6 minutes au lieu de 3,
pas un gel ni un plantage) mais ne satisfait pas littéralement le critère de sortie écrit.

- **Décision à prendre avec l'utilisateur avant de rouvrir le lot 1** : accepter l'écart tel
  que documenté (le critère étant partiellement hors du contrôle de l'application — Windows
  Defender), ou investir du temps supplémentaire dans la parallélisation du scan. Cette
  décision n'a pas été prise ; elle n'empêche pas de commencer le lot 2.

### 5.3 Fonctionnalités déjà commencées

Aucune fonctionnalité n'est dans un état « à moitié faite » en dehors de DiskPilot
(entièrement traité) et des réserves déjà listées en 3.2 (réglage `min_duplicate_size_bytes`
non exposé en interface, suppression définitive non câblée).

### 5.4 Fonctionnalités prioritaires restantes

Dans l'ordre du plan de livraison (section 1.4), **lot par lot, un seul à la fois** :

1. **Lot 2 — NetWatch (v0.3).** Fichiers à créer : `services/netwatch/`,
   `integrations/windows/network/` (ICMP via `IcmpSendEcho2`, pas de droits admin, Native
   WiFi), `integrations/network/` (dnspython), modèles `metrics.db` (première révision
   Alembic pour cette base — actuellement sans schéma, ADR-0008), page `NetWatchPage` réelle.
   Prérequis : ajouter `dnspython` et `pyqtgraph` à `pyproject.toml` avec justification dans
   `docs/dependances.md` (déjà le cas pour `psutil` au lot 1 — suivre le même modèle). Risque
   principal : l'API ICMP sans droits admin (`IcmpSendEcho2`) est documentée dans le cahier
   des charges mais jamais testée dans ce code. Critère de réussite : 24 h de surveillance
   sans fuite mémoire, classification des coupures testée (section 8 du cahier des charges).

2. **Lot 3 — Tableau de bord et recherche (v0.4).** Dépend du lot 2 (carte Réseau a besoin de
   NetWatch réel) mais pas uniquement : la carte Stockage peut déjà s'appuyer sur DiskPilot
   (lot 1, terminé). FTS5 à câbler pour la première fois.

3. Lots 4 à 7 (ClipVault, ScreenText, LogDoctor, AppManager) : chacun indépendant des autres
   modules métier, mais tous dépendent du socle (terminé).

4. **Lot 8 — Finitions** : dépend de tous les précédents.

### 5.5 Améliorations techniques

- Parallélisation du scan DiskPilot (voir 5.2), si la performance redevient une priorité.
- Vérifier que `pydantic-settings` et `hypothesis` (déjà en dépendances) sont réellement
  utilisés au fur et à mesure des lots qui en ont besoin, ou retirés s'ils ne servent jamais
  (actuellement listés mais pas utilisés dans le code, à vérifier lot par lot).
- Exposer `DiskPilotSettings` dans un onglet `SettingsPage` (actuellement seuls Général et
  Apparence existent).

### 5.6 Tests et stabilisation

Rien de spécifique en attente pour le code déjà livré (lots 0 et 1) — `scripts/test.ps1
-Integration -Coverage` est vert. À surveiller pour les lots suivants : le canari de
performance (`test_scan_performance_canary.py`) a un seuil volontairement bas (500
fichiers/s) à cause de l'interférence Defender constatée sur cette machine — **vérifier si
le même seuil reste pertinent sur le nouvel ordinateur** (une machine différente, avec ou
sans la même configuration antivirus, pourrait se comporter différemment).

### 5.7 Préparation de la livraison

Hors de portée avant le lot 8 (Finitions) : installateur Inno Setup, archive portable,
procédure de mise à jour, rapport de validation final (section 20 du cahier des charges).

---

## 6. Problèmes et solutions déjà rencontrés (pour éviter de les refaire)

### 6.1 Bug de performance réel dans `is_excluded` (lot 1, corrigé)

- **Symptômes :** un scan réel d'1 000 000 de fichiers prenait 697,6 s (budget : 180 s), un
  facteur ~3,9× au-dessus de la cible, malgré un micro-benchmark isolé antérieur qui laissait
  croire que le seul compromis sur la détection des liens physiques suffirait.
- **Cause identifiée :** `services/diskpilot/exclusions.py::is_excluded` appelait
  `Path.resolve()` sur **chaque** entrée de répertoire, **et** recalculait
  `scan_root.resolve()` à **chaque appel** (alors que la racine du scan ne change jamais
  pendant un scan). `Path.resolve()` effectue un aller-retour disque réel sous Windows
  (~230 µs/appel mesuré), ce qui en faisait le poste de coût dominant sur 1M d'entrées.
- **Correction appliquée :** comparaison directe des chemins sans `.resolve()` — les chemins
  fournis par `os.scandir` à partir d'une racine absolue sont déjà absolus et ne contiennent
  jamais de segment `..`, et la comparaison `PureWindowsPath` est déjà insensible à la casse.
- **Fichiers concernés :** `src/nexusdesk/services/diskpilot/exclusions.py`.
- **Résultat des tests :** `is_excluded` mesuré à ~1421 fichiers/s avant correction, ~8173
  fichiers/s après (sur un échantillon de 5000 fichiers, en isolation). Scan complet à 1M
  fichiers : 697,6 s → 362,1 s.
- **Risque de réapparition :** faible si le code n'est pas modifié sans relire l'ADR-0011 ;
  élevé si quelqu'un réintroduit un appel `.resolve()` dans une fonction appelée par entrée
  de fichier pendant un parcours à grande échelle sans refaire de mesure réelle à l'échelle.
  **Leçon générale pour la suite du projet :** un micro-benchmark isolé sur un échantillon
  réduit (ici ~100 000 fichiers) peut dissimuler un coût qui ne devient dominant qu'à pleine
  échelle (1M) — toujours valider au volume réel annoncé par le cahier des charges, pas
  seulement par extrapolation.

### 6.2 Coût du ramasse-miettes cyclique Python à grande échelle (lot 1, atténué)

- **Symptômes :** même après la correction 6.1, le scan restait à 362,1 s, encore ~2× au-dessus
  de la cible.
- **Cause identifiée :** jusqu'à 1 000 000 d'objets `FileNode` vivants simultanément
  (`FolderNode.files` n'est jamais plafonné, à l'inverse des 1000 plus gros fichiers
  persistés) ; le ramasse-miettes cyclique de CPython balaie périodiquement tous les objets
  suivis, un coût qui croît avec leur nombre. Aucun cycle de référence n'existe dans ce
  modèle de données (pas de référence arrière parent↔enfant), donc le comptage de références
  (mécanisme principal de CPython) suffit à libérer la mémoire correctement sans lui.
- **Correction appliquée :** `gc.disable()` au début du parcours
  (`scanner.py::build_scan_task`), `gc.enable()` dans un `finally` (donc même en cas
  d'annulation).
- **Fichiers concernés :** `src/nexusdesk/services/diskpilot/scanner.py`.
- **Résultat des tests :** 362,1 s → 246,3 s mesuré en isolation (avec désactivation du GC
  externe au moment du test) ; 341,1 s dans la mesure finale combinée (voir 6.4 sur l'écart).
- **Risque de réapparition :** nul tant que le modèle de données DiskPilot ne crée pas de
  cycle de référence. Si un futur lot ajoute une structure avec des références circulaires
  (ex. un arbre bidirectionnel parent↔enfant), revérifier que `gc.disable()` reste sûr à cet
  endroit précis.

### 6.3 Appel systématique de `get_size_on_disk` (lot 1, corrigé)

- **Symptômes :** coût supplémentaire mesuré à ~20 % par rapport à un simple `os.stat()`
  (5433 f/s avec l'appel systématique contre 6760 f/s sans, sur 100 000 fichiers réels).
- **Cause identifiée :** l'appel Win32 `GetCompressedFileSize` (via `get_size_on_disk`,
  `integrations/windows/filesystem.py`) était appelé pour **chaque** fichier, alors que seuls
  les fichiers compressés ou creux (NTFS) ont une taille sur disque réellement différente de
  leur taille logique.
- **Correction appliquée :** appel conditionné à
  `size_on_disk_may_differ_from_logical_size(stat_result.st_file_attributes)` (masque
  `FILE_ATTRIBUTE_COMPRESSED`/`SPARSE_FILE`, déjà disponible sans appel supplémentaire) ;
  sinon, `size_on_disk = stat_result.st_size`.
- **Fichiers concernés :** `src/nexusdesk/services/diskpilot/scanner.py`.
- **Risque de réapparition :** faible. Compromis documenté dans `ADR-0011` et couvert par un
  test unitaire explicite (`test_ordinary_file_size_on_disk_skips_the_expensive_call`).

### 6.4 Variance de performance due à Windows Defender (lot 1, constatée, non corrigée)

- **Symptômes :** des mesures répétées du même code, sur la même machine, donnaient des
  résultats très différents (debit mesuré entre ~860 et ~4059 fichiers/s selon l'exécution),
  y compris le canari de régression automatisé qui échouait de façon non reproductible à un
  seuil initial de 2000 fichiers/s.
- **Cause identifiée (plausible, pas certaine) :** `Get-MpPreference` confirme la protection
  temps réel de Windows Defender **active**, sans exclusion configurée pour les dossiers de
  test. Un antivirus à analyse sur accès peut intercepter chaque appel `os.stat`/
  `GetCompressedFileSize` de façon non déterministe.
- **Correction appliquée :** aucune sur Defender lui-même (désactiver une protection Windows
  dépasse le périmètre et l'autorisation de la session — explicitement interdit par le
  cahier des charges, section 16 : « Aucune désactivation de protection Windows »). Le seuil
  du canari de régression a été abaissé de 2000 à 500 fichiers/s pour rester fiable malgré
  cette variance, tout en restant largement au-dessus du débit d'une vraie régression
  algorithmique.
- **Fichiers concernés :** `tests/integration/windows/test_scan_performance_canary.py`.
- **Risque de réapparition :** élevé sur toute machine avec un antivirus à analyse en temps
  réel actif et sans exclusion. **Sur le nouvel ordinateur, si une validation de performance
  à grande échelle est refaite, s'attendre à la même variance** et, si besoin, envisager de
  demander à l'utilisateur d'ajouter une exclusion Defender pour le dossier de test (ne
  jamais le faire sans autorisation explicite).

### 6.5 Hook pre-commit mypy et commits incrémentaux (lot 1, contourné — pas un bug du code)

- **Symptômes :** plusieurs tentatives de `git commit` avec seulement un sous-ensemble de
  fichiers stagés échouaient avec des erreurs mypy du type « module X n'a pas d'attribut Y »,
  alors que le code final (tous fichiers réunis) était correct.
- **Cause identifiée :** `.pre-commit-config.yaml` configure le hook mypy avec
  `pass_filenames: false` (`entry: uv run mypy src`) — il type-vérifie **tout** `src/`
  indépendamment des fichiers réellement stagés pour ce commit. Pre-commit « remise de côté »
  (stash) les modifications **suivies mais non stagées**, mais laisse en place les
  **nouveaux fichiers non suivis** : un commit qui stage un fichier A dépendant d'un symbole
  défini dans un fichier B modifié-mais-non-stagé-dans-ce-commit échoue, parce que B est
  remis à son état d'avant pendant que A (nouveau, non suivi) reste présent.
- **Correction appliquée :** pas une correction de code — réorganisation de l'ordre des
  commits pour que chaque commit soit auto-cohérent (les fichiers qui dépendent d'un symbole
  sont stagés avec le fichier qui le définit).
- **Risque de réapparition :** élevé si de futurs commits incrémentaux séparent un nouveau
  fichier de sa dépendance modifiée. **Leçon pour la suite** : en cas d'échec mypy pendant un
  commit qui ne touche « que » quelques fichiers, vérifier d'abord si un autre fichier modifié
  mais non stagé est la vraie cause, avant de suspecter le code lui-même.

### 6.6 Vulnérabilité pytest (lot 0, corrigée)

- **Symptômes :** `pip-audit` signalait PYSEC-2026-1845 sur pytest 8.4.2.
- **Correction appliquée :** mise à jour vers pytest 9.1.1.
- **Fichiers concernés :** `pyproject.toml`, `uv.lock`.
- **Résultat des tests :** `pip-audit` vert ensuite, confirmé encore au lot 1.
- **Risque de réapparition :** faible, mais **toujours relancer `pip-audit` au nouvel
  ordinateur** après `uv sync` — une nouvelle CVE peut apparaître entre-temps.

### 6.7 Autres limites découvertes (lot 0, non bloquantes)

- Le `python.exe` du venv créé par `uv` est un lanceur qui respawn un processus enfant réel :
  un outillage de diagnostic qui cherche une fenêtre par PID doit cibler le **PID enfant**,
  pas celui de `Start-Process`. Non-problème pour l'exécutable packagé (binaire natif direct).
- Les stubs `types-pywin32` typent certains handles retournés (`PyHANDLE`) comme incompatibles
  avec les paramètres `int` attendus par d'autres fonctions win32 : des `# type: ignore`
  ciblés et documentés sont nécessaires (`single_instance.py`, `filesystem.py`). **Ce n'est
  pas une erreur de code à corriger, c'est une limitation connue des stubs.**
- Simuler un vrai placeholder OneDrive via `SetFileAttributesW` échoue avec
  `ERROR_FILE_NOT_FOUND` sur un fichier NTFS ordinaire (vérifié empiriquement, lot 1) : cet
  attribut est géré par le pilote Cloud Filter réel, pas positionnable par un appel direct.
  **Ne pas perdre de temps à essayer de le simuler autrement sans un vrai client OneDrive.**

---

## 7. Installation sur le nouvel ordinateur

### 7.1 Versions exactes des outils (constatées sur cette machine)

| Outil | Version constatée | Source |
| --- | --- | --- |
| Windows | 11 Home, build 26200 | `[System.Environment]::OSVersion` |
| Python | 3.12 (épinglé par uv, voir `.python-version`) | `.python-version` = `3.12` |
| uv | 0.11.18 | `uv --version` |
| PowerShell | 7.6.8 (mentionné dans `docs/journal-des-lots.md`, lot 0) | journal |
| Disque de développement | SSD NVMe (confirmé via `Get-PhysicalDisk`) | utilisé pour la validation de performance lot 1 — **à revérifier sur le nouvel ordinateur**, le type de disque affecte directement le critère de sortie du lot 1 |

**Non déterminé :** la configuration exacte de Windows Defender (exclusions, version des
définitions) sur le nouvel ordinateur. À vérifier si une nouvelle validation de performance
DiskPilot est entreprise (voir section 6.4).

### 7.2 Procédure d'installation (PowerShell, Windows)

```powershell
# 1. Cloner ou copier le dépôt sur le nouvel ordinateur, puis :
cd "chemin\vers\NexusDesk - App"

# 2. Installer uv si absent (voir https://docs.astral.sh/uv/)
#    Le script install-dev.ps1 vérifie sa présence et échoue explicitement sinon.

# 3. Préparer l'environnement (installe Python 3.12 via uv, synchronise toutes les
#    dépendances dev depuis uv.lock, installe les hooks pre-commit) :
./scripts/install-dev.ps1

# 4. Vérifier que tout est sain :
./scripts/check.ps1

# 5. Lancer les tests (unitaires + interface + intégration Windows + couverture) :
./scripts/test.ps1 -Integration -Coverage

# 6. Lancer l'application depuis les sources en mode développeur :
./scripts/run.ps1 -Dev
```

Ces scripts existaient déjà et sont testés (lot 0 puis lot 1) — ils n'ont pas été modifiés
pour les besoins de ce document.

### 7.3 Variables d'environnement

| Variable | Rôle | À définir ? |
| --- | --- | --- |
| `NEXUSDESK_ALLOW_IPC_QUIT` | Autorise la commande IPC `QUIT` (réservée à `scripts/smoke-test.ps1`, ADR-0009) | Non, sauf pour relancer ce script précis |
| `SYSTEMDRIVE` | Lue par `services/diskpilot/exclusions.py` pour déterminer le volume système | Définie nativement par Windows, jamais à positionner manuellement |

**Aucune clé API, aucun secret, aucun jeton n'est utilisé par le code actuel** (lots 0 et 1).
Si `/graphify` ou un outil similaire doit être réessayé sur le nouvel ordinateur, une clé
`GEMINI_API_KEY` (ou équivalent) serait nécessaire, mais **cela reste hors du périmètre du
produit NexusDesk lui-même** — à ne configurer que si l'utilisateur le demande
explicitement.

### 7.4 Bases de données et migrations

Les bases SQLite (`nexusdesk.db`, `metrics.db`, `diskpilot_hash_cache.db`) sont créées et
migrées **automatiquement au premier démarrage** de l'application (`app.py::Application.__init__`,
via `database/migration_runner.py` et `CacheBase.metadata.create_all`). **Aucune commande
manuelle n'est nécessaire.** Elles vivent sous `%LOCALAPPDATA%\NexusDesk\data\` (ou à côté de
l'exécutable en mode portable, si un fichier `portable.flag` y est présent — mécanisme prévu
par le cahier des charges, section 14, implémenté dans `core/paths.py`).

**Sur le nouvel ordinateur, ces fichiers n'existeront pas** (ils sont explicitement exclus de
Git — `*.db`, `*.db-wal`, etc., dans `.gitignore`) : l'application les recréera vides à son
premier lancement. **Aucune donnée utilisateur à transférer** pour ce projet à ce stade (le
développement n'a jamais fait tourner l'application avec des données réelles autres que les
scans de test, déjà nettoyés).

### 7.5 Fichiers ignorés par Git à régénérer (pas à transférer)

D'après `.gitignore`, ces éléments sont **recréés automatiquement** et ne doivent pas être
copiés manuellement (ou peuvent l'être pour gagner du temps, sans risque) :
- `.venv/` — régénéré par `uv sync` (`install-dev.ps1`).
- `dist/`, `build/` — régénérés par `scripts/build.ps1` si besoin (pas nécessaire pour le
  développement courant).
- `*.db`, `*.db-wal`, `*.db-shm`, `*.db-journal` — régénérés au premier lancement.
- `logs/`, `*.log` — régénérés automatiquement.
- `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`, `htmlcov/`, `.coverage` — caches d'outils,
  régénérés à chaque exécution, sans impact fonctionnel.
- `reports/` — **attention** : ce dossier contient le plan de lot 1
  (`spicy-giggling-taco.md`), **non versionné**. S'il n'est pas copié manuellement, ce plan
  sera perdu (il n'affecte pas le fonctionnement du code, seulement la traçabilité de la
  décision de conception du lot 1, déjà résumée dans les ADR et ce document).
- `.claude/settings.local.json` — configuration locale propre à la machine actuelle ; **ne
  pas transférer tel quel**, le nouvel ordinateur a son propre système de permissions/outils
  (codebase-memory-mcp, Basic Memory, hooks).

### 7.6 Logiciels externes indispensables

Pour les lots **déjà livrés** (0 et 1) : aucun logiciel externe au-delà de Python/uv/Git —
tout le reste (pywin32, psutil, PySide6...) est installé par `uv sync`.

Pour les **lots suivants**, le cahier des charges exige déjà, en anticipation :
- **Lot 2 (NetWatch)** : aucun logiciel externe (API Windows natives + dnspython).
- **Lot 5 (ScreenText)** : Tesseract 5.x (installation séparée, détectée et diagnostiquée par
  l'application, jamais embarquée) ; Windows OCR (modules linguistiques Windows, déjà
  présents sur un Windows standard).
- **Lot 7 (AppManager)** : module PowerShell `Microsoft.WinGet.Client` (installable via
  `Install-Module`, l'application doit en proposer la commande, jamais l'exécuter seule sans
  confirmation).
- **Lot 8 (packaging)** : Inno Setup (pour l'installateur, pas encore utilisé).

### 7.7 Build et tests

Déjà couvert en 7.2. Résumé des résultats constatés en fin de lot 1 sur cette machine
(peuvent différer sur le nouvel ordinateur, notamment pour la performance — section 6.4) :
- `scripts/check.ps1` : **vert**.
- `scripts/test.ps1 -Integration -Coverage` : **vert**, 98 tests passés + 1 neutralisé
  honnêtement (`skipif`, droits symlink insuffisants — peut passer ou non selon que le mode
  développeur Windows est activé sur le nouvel ordinateur), couverture globale 58 %,
  couverture de `services/diskpilot/` 90,4 %.

### 7.8 Différences possibles entre les deux environnements (à surveiller)

- **Mode développeur Windows** (nécessaire pour `os.symlink` sans élévation) : état non
  déterminé sur le nouvel ordinateur. Si désactivé, un test (`test_symlink_is_recorded_as_link_and_never_followed`)
  se neutralise proprement (`skipif`), ce n'est pas un échec.
- **Windows Defender** (exclusions, charge de fond) : affecte directement toute mesure de
  performance DiskPilot (section 6.4) — à revérifier si pertinent.
- **Type de disque** (SSD NVMe vs autre) : le critère de sortie du lot 1 est explicitement
  « sur SSD NVMe » — si le nouvel ordinateur utilise un disque différent, les chiffres de
  `docs/journal-des-lots.md` ne sont pas transposables tels quels.
- **Système de mémoire Claude Code** (codebase-memory-mcp, Basic Memory, hooks) : absent de
  cette machine de développement (le répertoire mémoire local pour ce projet est vide, voir
  section 0). Sur le nouvel ordinateur, ce document est précisément destiné à amorcer cette
  mémoire.

---

## 8. Synthèse courte pour chargement automatique en mémoire

> Section pensée pour être indexée rapidement par `codebase-memory-mcp` / Basic Memory.

**NexusDesk** est une boîte à outils Windows 11 locale (Python 3.12 + PySide6), sans
télémétrie, livrée par 9 lots (0 à 8). **État au 2026-10-27 20:07 (dernier commit
`e36cda5`, branche `lot-1-diskpilot`, non fusionnée dans `main`) :**
- **Lot 0 (Socle, v0.1) : terminé et vérifié.** Architecture en couches (`ui` →
  `viewmodels` → `services` → `repositories`/`database` ; `core`/`config`/`models`
  transverses), SQLite+Alembic, gestionnaire de tâches `QThreadPool`, instance unique,
  design system à jetons, shell, exécutable packagé testé.
- **Lot 1 (DiskPilot, v0.2) : terminé avec réserve.** Module complet (scan, treemap,
  doublons, suppression Corbeille) et testé, **mais le critère de performance (1M fichiers
  < 180 s) n'est pas garanti** (meilleure mesure : ~246-341 s selon les conditions,
  probablement freiné par Windows Defender). Un vrai bug de performance (`Path.resolve()`
  appelé par entrée dans `exclusions.py::is_excluded`) a été trouvé et corrigé pendant cette
  validation — voir `ADR-0011` et section 6.1 de ce document.
- **Lots 2 à 8 (NetWatch, Dashboard, ClipVault, ScreenText, LogDoctor, AppManager,
  Finitions) : non commencés**, pages `PlaceholderPage` honnêtes.
- **Règles de méthode imposées par le cahier des charges et suivies jusqu'ici** : un lot par
  session, choix réversibles décidés seul et consignés en ADR (14 ADR à ce jour), commits
  Git petits en français à l'impératif, compte rendu honnête en 4 parties à chaque fin de
  lot (`docs/journal-des-lots.md`), jamais de bouton sans fonction réelle, jamais de données
  inventées, jamais de résultat de test non exécuté affiché comme réussi.
- **Décisions clés déjà prises (ADR)** : tube nommé pour l'IPC (ADR-0002), table clé/valeur
  pour les paramètres (ADR-0003), QSS généré en Python natif sans Jinja2 (ADR-0004),
  `SHFileOperation` plutôt qu'`IFileOperation` pour la Corbeille (ADR-0010), détection
  conditionnelle des liens physiques et de la taille sur disque (ADR-0011), sous-paquet
  `ui/pages/diskpilot/` plutôt qu'un fichier plat (ADR-0012), rétention SQL par `DELETE` +
  cascade FK (ADR-0013), cache d'empreintes dans une base séparée hors Alembic (ADR-0015).
- **Cahier des charges complet** : disponible dans `docs/cahier-des-charges-v2.md`, fichier
  versionné du dépôt (voir section 0).

---

## 9. INSTRUCTIONS DE REPRISE SUR LE NOUVEAU PC

### Ce qu'est le projet

NexusDesk : boîte à outils Windows 11 locale en Python 3.12 + PySide6, livrée par lots. Lis
la section 1 de ce document et le cahier des charges complet (`docs/cahier-des-charges-v2.md`)
avant toute action.

### Où en est le projet

Lot 0 (socle) et lot 1 (DiskPilot) terminés et commités sur la branche `lot-1-diskpilot`
(non fusionnée dans `main`). Le lot 1 a une réserve documentée (performance à grande
échelle, section 3.2 et 6.1-6.4) — ce n'est pas un bug caché, c'est consigné honnêtement.

### Où reprendre exactement

Deux choix légitimes, à soumettre à l'utilisateur plutôt qu'à décider seul :
1. Fusionner `lot-1-diskpilot` dans `main`, puis démarrer le **lot 2 (NetWatch)**.
2. Rouvrir le lot 1 pour tenter de fiabiliser le critère de performance (parallélisation du
   scan), si l'utilisateur juge que c'est prioritaire avant de passer au lot 2.

**Ne décide pas cela seul** : c'est exactement le type de choix que le cahier des charges
(section 21.3) range parmi les décisions à soumettre à l'utilisateur, pas à trancher
unilatéralement.

### Premières vérifications à effectuer

1. `git log --oneline -5` et `git status` — confirmer l'état exact du dépôt sur cette
   machine (peut avoir changé depuis la génération de ce document si l'utilisateur a
   transféré le dépôt différemment).
2. `git branch -a` — confirmer que `lot-1-diskpilot` est bien la branche active et que
   `main` n'a pas évolué autrement.
3. `./scripts/install-dev.ps1` puis `./scripts/check.ps1` puis
   `./scripts/test.ps1 -Integration -Coverage` — confirmer que l'environnement fonctionne
   sur cette nouvelle machine avant toute nouvelle modification.
4. Vérifier `Get-MpPreference` (Windows Defender) et le type de disque si une validation de
   performance DiskPilot doit être refaite (section 6.4 et 7.8).
5. Vérifier la présence de `docs/cahier-des-charges-v2.md` (ajouté au dépôt après la
   rédaction initiale de ce document, voir section 0) ; s'il manque malgré tout, demander à
   l'utilisateur de le fournir à nouveau plutôt que de deviner son contenu.

### Premières tâches à réaliser

Selon la décision de l'utilisateur (voir « Où reprendre exactement ») : soit démarrer le lot
2 en suivant exactement la même méthodologie que les lots 0 et 1 (plan court, ADR pour les
choix réversibles, tests réels, compte rendu honnête en 4 parties), soit investiguer la
parallélisation du scan DiskPilot.

### Erreurs et décisions à connaître avant de commencer

Lire entièrement la section 6 de ce document avant de toucher à
`services/diskpilot/scanner.py` ou `exclusions.py` — plusieurs optimisations de performance
non évidentes y sont déjà appliquées et documentées (ADR-0011) ; ne pas les défaire par
accident en « simplifiant » le code.

### Fichiers à lire en priorité

1. Ce document (`PROJECT_HANDOVER.md`).
2. Le cahier des charges complet (`docs/cahier-des-charges-v2.md`).
3. `docs/journal-des-lots.md` (historique honnête lot par lot).
4. `docs/architecture.md` et `docs/adr/` (décisions structurantes).
5. `reports/spicy-giggling-taco.md` si transféré (plan détaillé du lot 1, utile comme
   gabarit pour écrire le plan du lot 2).

### Commandes à exécuter en premier

```powershell
cd "chemin\vers\NexusDesk - App"
git log --oneline -10
git status
./scripts/install-dev.ps1
./scripts/check.ps1
./scripts/test.ps1 -Integration -Coverage
```

### Éléments à ne pas modifier sans vérification

- `services/diskpilot/scanner.py` et `exclusions.py` : optimisations de performance
  non évidentes, documentées en ADR-0011 — toute simplification doit être revalidée par une
  mesure réelle à l'échelle (pas seulement un micro-benchmark).
- `.pre-commit-config.yaml` : le hook mypy type-vérifie tout `src/` indépendamment des
  fichiers stagés (`pass_filenames: false`) — ce comportement a surpris pendant le lot 1
  (section 6.5), ce n'est pas un bug à corriger, mais à connaître avant de committer par
  petits morceaux.
- `pyproject.toml` (section `[tool.importlinter]`) : les 5 contrats de couches sont le
  mécanisme de vérification automatique de l'architecture imposée par le cahier des charges
  (section 4) — ne pas les affaiblir pour faire passer un import de commodité.
- Les migrations déjà appliquées (`0001_initial.py`, `0002_diskpilot.py`) : jamais modifier
  une migration déjà livrée ; toujours en ajouter une nouvelle (convention Alembic standard,
  déjà respectée dans ce projet).

---

## Message de reprise prêt à copier dans la nouvelle session Claude Code

```
Je reprends le projet NexusDesk (boîte à outils Windows 11 locale, Python 3.12 + PySide6,
livrée par lots). Lis en entier le fichier PROJECT_HANDOVER.md à la racine du projet avant
toute action — il contient l'état réel du projet, l'historique honnête du développement, les
problèmes déjà résolus et la feuille de route.

État : lot 0 (Socle) et lot 1 (DiskPilot) terminés et commités sur la branche
lot-1-diskpilot (non fusionnée dans main). Le lot 1 a une réserve documentée sur le critère
de performance à grande échelle (section 3.2 et 6 du document de transmission) — ce n'est
pas un bug caché, c'est consigné honnêtement dans docs/journal-des-lots.md et ADR-0011.

Avant de faire quoi que ce soit : exécute les vérifications de la section 9 du document de
transmission (git log/status, scripts/install-dev.ps1, check.ps1, test.ps1 -Integration
-Coverage), confirme-moi que l'environnement est sain sur cette machine, puis demande-moi
explicitement si je veux (a) fusionner lot-1-diskpilot dans main puis démarrer le lot 2
(NetWatch), ou (b) rouvrir le lot 1 pour fiabiliser la performance avant de continuer. Ne
décide pas ça seul.

Le cahier des charges complet est dans docs/cahier-des-charges-v2.md — lis-le avant de
commencer.
```

---

**Confirmation finale** (voir aussi le message de clôture dans la conversation) :
- Chemin exact du document : `c:\Users\remid\Desktop\NexusDesk\NexusDesk - App\PROJECT_HANDOVER.md`
- Date de génération : 2026-11-01
- Dernière tâche identifiée avant la génération de ce document : clôture du lot 1 DiskPilot
  (commit `e36cda5`, 2026-10-27 20:07:25 +01:00), suivie d'une tentative infructueuse de
  `/graphify` (sans impact sur le dépôt).
