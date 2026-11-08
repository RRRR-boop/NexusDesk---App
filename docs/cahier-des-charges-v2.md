# NexusDesk — Cahier des charges v2

Oct 25, 2026 · @Remi

NexusDesk est une boîte à outils Windows 11 locale, gratuite et sans télémétrie qui réunit six modules (AppManager, NetWatch, ScreenText, LogDoctor, DiskPilot, ClipVault) autour d'un tableau de bord, d'une palette de commandes et d'une recherche globale. Cette v2 corrige les erreurs techniques de la v1, comble ses lacunes et ajoute les améliorations qui feront la différence au quotidien.

## Ce qui change par rapport à la v1

La v2 garde l'esprit de la v1 (local, gratuit, prudent, honnête) mais corrige cinq erreurs techniques et ajoute une couche produit qui manquait.

| Domaine | v1 | v2 | Raison |
| --- | --- | --- | --- |
| Périmètre | Six modules complets d'un coup | Livraison par lots, chaque lot utilisable seul | Éviter six outils moyens |
| Architecture | Processus unique | Processus résident + assistant élevé à la demande | Un processus Python ne peut pas s'élever en cours de route |
| Résidence | Non prévue | Icône de zone de notification, instance unique, agent permanent | ClipVault et le raccourci OCR doivent tourner fenêtre fermée |
| Migrations | « Migrations versionnées » | Alembic + sauvegarde via l'API backup de SQLite | Outil standard de SQLAlchemy |
| Recherche globale | Non spécifiée | SQLite FTS5 + palette de commandes Ctrl+K | Rapide, locale, sans dépendance |
| AppManager | Parsing de la sortie winget | Module PowerShell Microsoft.WinGet.Client (sortie objet) | La sortie texte est tronquée et traduite |
| NetWatch | Ping non précisé | IcmpSendEcho (iphlpapi), sans droits admin | Les sockets ICMP bruts exigent l'admin |
| ScreenText | Tesseract « détecte la langue » | Tesseract détecte l'écriture ; Windows OCR en moteur alternatif | Tesseract n'a pas de détection de langue |
| DiskPilot | Hachage de tous les doublons candidats | Exclusion des fichiers OneDrive à la demande, suppression vers la Corbeille | Le hachage déclencherait leur téléchargement |
| ClipVault | « Détecter les mots de passe si fiable » | Respect des formats d'exclusion posés par les gestionnaires de mots de passe | Signal standard et fiable |
| Chiffrement | « Protéger les données » | DPAPI sur les historiques ClipVault et OCR | Lié à la session Windows, sans mot de passe |
| Environnement | Python + pip | uv, lock reproductible, Python 3.12 | Installations rapides et déterministes |
| UX | Navigation latérale seule | Palette de commandes, raccourcis, actions rapides, onboarding | Usage quotidien au clavier |
| Design | Description textuelle | Design system à jetons, thèmes sombre et clair, Mica | Cohérence et maintenabilité |
| Distribution | Exécutable unique | Installateur Inno Setup + version portable, mises à jour vérifiées | Désinstallation propre, données préservées |

## 1. Mission, principes et périmètre

NexusDesk doit devenir l'outil qu'on ouvre chaque jour pour comprendre et entretenir son PC, sans compte, sans abonnement et sans envoyer de données. Sa valeur ne tient pas à chaque module pris isolément, mais à leur réunion : un seul agent, un seul historique, une seule recherche.

### Principes non négociables

1. **Local d'abord.** Aucune donnée ne quitte le PC, sauf requête explicite (mise à jour winget, téléchargement d'un modèle OCR, test réseau vers une cible choisie).
2. **Honnêteté des données.** Aucune valeur inventée. Une collecte qui échoue s'affiche comme indisponible, avec la raison.
3. **Faits séparés des hypothèses.** Toute interprétation (diagnostic, doublon probable, cause de coupure) est présentée comme telle.
4. **Rien d'irréversible sans confirmation.** Suppressions vers la Corbeille par défaut, aperçu de la commande avant exécution.
5. **Moindre privilège.** L'interface ne tourne jamais en administrateur. L'élévation passe par un assistant dédié, à la demande, avec une explication.
6. **Interface jamais figée.** Toute opération de plus de 100 ms s'exécute en tâche de fond, annulable.
7. **Aucun bouton factice.** Une fonction non terminée est absente de l'interface, pas grisée sans raison.

### Périmètre de la v1.0

La v1.0 livre les six modules, le tableau de bord, la recherche globale et la palette de commandes. Sont hors périmètre v1.0 : images dans ClipVault, synchronisation entre PC, extensions tierces, multilingue (interface en français uniquement, mais chaînes externalisées pour une traduction future).

### Public visé

Un utilisateur à l'aise avec Windows, sans être administrateur système : il veut des réponses claires (« ma connexion a coupé 3 fois ce matin ») avant les détails techniques, qui restent accessibles d'un clic.

## 2. Environnement cible et contraintes

La cible est Windows 11 64 bits (22H2 ou plus récent) sur un PC standard ; aucune fonction ne dépend du GPU.

| Contrainte | Exigence |
| --- | --- |
| Système | Windows 11 x64 22H2+ ; Windows 10 22H2 toléré sans garantie |
| Matériel de référence | 16 Go de RAM, NVIDIA T1000 8 Go (non utilisée : Tesseract et Windows OCR tournent sur le processeur) |
| Empreinte | Fenêtre fermée : < 120 Mo de RAM et < 1 % de CPU ; fenêtre ouverte : < 300 Mo |
| Démarrage | Processus résident prêt en moins de 2 s ; fenêtre affichée en moins de 500 ms ensuite |
| Réseau | Fonctionnement complet hors ligne pour les fonctions locales ; Internet uniquement pour winget, les modèles OCR et les tests vers des cibles choisies |
| Comptes | Aucun compte, aucun abonnement, aucune clé API, aucune télémétrie, aucun rapport de plantage envoyé |
| Privilèges | Utilisateur standard pour tout l'usage courant ; élévation ponctuelle via l'assistant élevé, motif affiché |
| Écrans | Multi-écran et mise à l'échelle DPI mixte (100 % à 200 %) gérés |
| Langue | Interface en français ; dates, nombres et tailles au format fr-FR (1 234,5 Mo, 25/10/2026) |

Toute fonctionnalité qui exige l'administrateur (journal Security, désactivation d'un démarrage HKLM, désinstallation machine) est signalée par une icône de bouclier avant le clic.

## 3. Stack technique

La stack reste Python 3.12 + PySide6 (Qt Widgets), complétée par les outils qui manquaient à la v1 et allégée de ce qui posait un problème de licence ou de fiabilité. Chaque dépendance est justifiée ; toute nouvelle dépendance exige une ligne dans `docs/dependances.md` (rôle, licence, alternative écartée).

| Couche | Choix | Rôle | Licence |
| --- | --- | --- | --- |
| Langage | Python 3.12 | Logique applicative, typage strict | PSF |
| Environnement | uv + `uv.lock` | Venv, verrouillage, installation reproductible | MIT / Apache 2.0 |
| Interface | PySide6 6.8+ (Qt Widgets) | Fenêtres, modèles de tableaux, thèmes | LGPLv3 (liaison dynamique) |
| Graphiques | pyqtgraph | Courbes temporelles fluides (NetWatch, tableau de bord) | MIT |
| Base de données | SQLite (WAL, FTS5) | Stockage, index plein texte | Domaine public |
| ORM | SQLAlchemy 2.0 (typé) | Accès aux données via dépôts | MIT |
| Migrations | Alembic | Migrations versionnées | MIT |
| Configuration | pydantic v2 + pydantic-settings | Validation des paramètres et des entrées | MIT |
| Système | psutil | Volumes, interfaces, processus | BSD-3 |
| API Windows | pywin32 + ctypes | Registre, journaux, presse-papiers, DPAPI, Corbeille, ICMP | PSF / standard |
| WinRT | pywinrt (winrt-Windows.Media.Ocr, winrt-Windows.Graphics.Imaging) | Moteur OCR Windows intégré | MIT |
| OCR principal | Tesseract 5.x appelé en sous-processus (sortie TSV) | OCR multilingue local | Apache 2.0 |
| DNS | dnspython | Requêtes vers un serveur précis, timeouts fins | ISC |
| Tests | pytest, pytest-qt, pytest-cov, hypothesis | Unitaires, interface, propriétés des parseurs | MIT / MPL 2.0 |
| Qualité | Ruff (lint + format), mypy --strict, pre-commit | Style, types, hooks Git | MIT |
| Packaging | PyInstaller (mode dossier) + Inno Setup | Exécutable et installateur | GPL avec exception / libre |
| Icônes | Fluent UI System Icons (SVG) | Jeu d'icônes cohérent avec Windows 11 | MIT |
| Polices | Segoe UI Variable, Cascadia Mono (fournies par Windows) | Texte et données techniques | Système |

### Choix écartés et pourquoi

- **Qt Charts** : sous GPLv3 dans sa version libre, contrairement au cœur de Qt. Remplacé par pyqtgraph.
- **pytesseract** : simple surcouche de sous-processus ; un appel direct avec arguments en liste suffit et retire une dépendance.
- **PyQt-Fluent-Widgets** : joli mais sous GPLv3 pour un usage libre ; un design system maison sur QSS évite cette contrainte.
- **asyncio + qasync** : un seul modèle de concurrence est retenu (QThreadPool + gestionnaire de tâches, voir section 4) pour éviter de mélanger deux boucles d'événements.
- **Parsing de la sortie de winget.exe** : remplacé par le module PowerShell Microsoft.WinGet.Client, qui renvoie des objets.

### Alternative envisagée : C# / .NET 8 + WinUI 3

Si l'objectif devient une application diffusée largement, C# avec WinUI 3 serait plus natif : accès direct à WinGet (COM), à Windows OCR et à DPAPI, exécutable plus léger (environ 60 Mo contre 200 Mo), apparence Windows 11 sans effort. Python reste retenu pour la v1.0 parce que c'est la compétence de départ et que toutes les fonctions sont atteignables. L'architecture en couches (section 4) garde la logique métier indépendante de l'interface pour ne pas fermer cette porte.

## 4. Architecture

NexusDesk tourne en un processus résident (zone de notification + fenêtre créée à la demande) et lance un assistant élevé uniquement quand une opération l'exige. La logique métier ne dépend jamais de Qt Widgets, ce qui la rend testable sans interface.

### Processus

1. **Processus résident `NexusDesk.exe`** (utilisateur standard). Il porte l'icône de zone de notification, le raccourci global, l'écoute du presse-papiers, l'échantillonnage réseau et les tâches planifiées (rétention, sauvegardes). La fenêtre principale est créée à l'ouverture et ses pages sont déchargées à la fermeture.
2. **Assistant élevé `NexusDesk.Elevated.exe`**, lancé via `ShellExecuteEx` avec le verbe `runas`, donc après une invite UAC. Il n'accepte qu'une liste fermée de commandes (lire le journal Security, modifier une entrée de démarrage HKLM, lancer une désinstallation machine). Il communique par canal nommé dont l'ACL n'autorise que le SID de l'utilisateur courant, avec un jeton à usage unique transmis au lancement. Il s'arrête après 60 s d'inactivité.
3. **Sous-processus externes** : `tesseract.exe`, `powershell.exe` (module WinGet), `winget.exe`, toujours avec des arguments en liste, chemin absolu vérifié et timeout.

Une seule instance est autorisée (mutex nommé `Local\NexusDesk`). Un second lancement transmet sa demande à l'instance existante (ouvrir une page, lancer une capture) puis se termine.

### Couches et règles de dépendance

| Couche | Dossier | Peut importer | Ne doit jamais importer |
| --- | --- | --- | --- |
| Interface | `ui/` | `viewmodels/`, `core/` | `integrations/`, `database/` |
| Présentation | `viewmodels/` | `services/`, `core/` | `ui/`, `integrations/` |
| Métier | `services/` | `repositories/`, interfaces `Protocol` des intégrations, `core/` | Qt Widgets |
| Données | `repositories/`, `database/` | `models/`, `core/` | `services/`, `ui/` |
| Intégrations | `integrations/` | `core/` | `services/`, `ui/` |

Ces règles sont vérifiées automatiquement par import-linter dans la CI locale.

### Concurrence

Un gestionnaire de tâches unique (`core/tasks.py`) encapsule QThreadPool. Chaque tâche a :

- une **clé de déduplication** (ex. `diskscan:C:\Users\Remi`) qui empêche deux scans identiques ;
- un **jeton d'annulation** vérifié dans les boucles ;
- une **progression** (fraction, étape, message) publiée par signal Qt, limitée à 10 mises à jour par seconde ;
- un **résultat ou une erreur typée** (`DependencyMissing`, `PermissionDenied`, `Timeout`, `Cancelled`).

Le centre d'opérations de l'interface affiche toutes les tâches actives, avec annulation. Chaque fil de travail ouvre sa propre session SQLAlchemy ; les écritures passent par une file unique pour éviter les verrous SQLite.

### Arborescence

```
src/nexusdesk/
  __main__.py          point d'entrée, instance unique
  app.py               assemblage des dépendances
  core/                tâches, événements, erreurs, chemins, journalisation
  config/              schémas pydantic des paramètres
  database/            moteur, sessions, sauvegarde
    migrations/        Alembic
  models/              entités SQLAlchemy
  repositories/        un dépôt par agrégat
  services/            appmanager/, netwatch/, screentext/, logdoctor/, diskpilot/, clipvault/, search/, dashboard/
  integrations/
    windows/           registre, DPAPI, Corbeille, raccourcis, notifications toast
    winget/            module PowerShell WinGet
    network/           ICMP, ARP, DNS, TCP
    ocr/               Tesseract, Windows OCR
    clipboard/         écouteur, formats d'exclusion
    eventlog/          API EvtQuery
    storage/           parcours de dossiers, attributs NTFS
  elevated/            assistant élevé et protocole
  viewmodels/
  ui/
    shell/             fenêtre, navigation, palette, zone de notification
    pages/             une page par module + tableau de bord + paramètres
    components/        composants du design system
    theme/             jetons, QSS générés, icônes
  resources/
  knowledge/           fiches de diagnostic LogDoctor (YAML)
tests/   unit/ integration/ ui/ fixtures/
docs/    architecture, dépendances, permissions, ADR
scripts/ PowerShell
```

Chaque décision structurante est consignée dans un ADR (`docs/adr/0001-processus-resident.md`, etc.).

### Schéma d'ensemble

[embedded content: Architecture · 1 processus résident, 5 couches, 1 assistant élevé]

Chaque couche n'appelle que celle du dessous ; seul l'assistant élevé, lancé après une invite UAC, touche aux opérations réservées à l'administrateur.

## 5. Design system

L'apparence repose sur des jetons définis une seule fois (`ui/theme/tokens.py`) d'où sont générées les feuilles QSS ; aucun widget ne contient de couleur ou de taille codée en dur. Le thème sombre anthracite est le défaut, un thème clair est fourni, et l'option « Suivre Windows » bascule automatiquement.

### Couleurs (thème sombre)

| Jeton | Valeur | Usage |
| --- | --- | --- |
| `bg.base` | #16161A | Fond de fenêtre |
| `bg.surface` | #1E1E24 | Cartes, panneaux |
| `bg.raised` | #26262E | Survol, menus, boîtes de dialogue |
| `border.subtle` | #33333D | Séparateurs, contours de cartes |
| `text.primary` | #EDEDF2 | Texte principal |
| `text.secondary` | #A6A6B5 | Libellés, métadonnées |
| `text.disabled` | #6E6E7E | Texte inactif |
| `accent.primary` | #7C3AED (survol #8B5CF6) | Boutons principaux, sélection, focus |
| `accent.secondary` | #22D3EE | Données en direct, graphiques, liens |
| `status.success` | #34D399 | Opération réussie, connexion bonne |
| `status.warning` | #FBBF24 | Dégradation, attention |
| `status.danger` | #F87171 | Erreur, action destructive |

Contrastes vérifiés : texte principal et secondaire au moins 4,5:1 sur leurs fonds (WCAG AA) ; texte blanc sur `accent.primary` à 5,7:1. Un état n'est jamais signalé par la couleur seule : toujours une icône et un libellé.

### Typographie

| Style | Police | Taille / graisse | Usage |
| --- | --- | --- | --- |
| Titre de page | Segoe UI Variable Display | 28 px / 600 | En-tête de module |
| Titre de section | Segoe UI Variable | 20 px / 600 | Groupes, cartes larges |
| Sous-titre | Segoe UI Variable | 16 px / 600 | Titres de carte |
| Corps | Segoe UI Variable Text | 14 px / 400 | Texte courant, tableaux |
| Légende | Segoe UI Variable Small | 12 px / 400 | Métadonnées, aide |
| Données | Cascadia Mono | 13 px / 400 | Chemins, commandes, IP, identifiants d'événement |
| Chiffre clé | Segoe UI Variable Display | 32 px / 600, chiffres tabulaires | Valeurs du tableau de bord |

### Espacements, formes, mouvement

- Grille de 4 px : espacements 4, 8, 12, 16, 24, 32 ; marges de page 24 px ; écart entre cartes 16 px.
- Rayons : 4 px pour les contrôles, 8 px pour les cartes et boîtes de dialogue.
- Profondeur exprimée par la couleur de fond et un contour de 1 px, pas par des ombres lourdes.
- Animations de 150 à 200 ms, courbe ease-out, uniquement pour les transitions d'état (ouverture de panneau, apparition d'un toast). Désactivées si l'option Windows « Effets d'animation » est coupée.
- Effet Mica (fond translucide Windows 11) via `DwmSetWindowAttribute` sur la barre latérale, avec repli sur `bg.base` si indisponible.

### Composants

| Composant | Comportement attendu |
| --- | --- |
| Barre de navigation | Repliable (icônes seules / icônes + libellés), badge par module (mises à jour, erreurs), raccourcis Ctrl+1 à Ctrl+7 |
| Carte de statistique | Valeur, unité, tendance, mini-graphique, horodatage de la donnée, état indisponible explicite |
| Tableau de données | QTableView virtualisé, tri, filtre par colonne, choix des colonnes, vues enregistrées, sélection multiple, menu contextuel, export |
| Barre de filtres | Puces de filtres actifs, effacement en un clic, compteur de résultats |
| Aperçu de commande | Bloc monospace de la commande exacte, bouton Copier, description de l'effet attendu |
| Boîte de confirmation | Liste des éléments concernés, total (nombre, taille), action par défaut non destructive, saisie de confirmation au-delà de 100 éléments ou 10 Go |
| Bandeau d'information | Info, succès, avertissement, erreur ; action associée (Réessayer, Ouvrir les paramètres) |
| État vide | Illustration légère, phrase utile, action principale (« Lancer un premier scan ») |
| Squelette de chargement | Gabarits gris animés à la place des données, jamais de valeurs factices |
| Pastille Fait / Hypothèse | Distingue visuellement les faits collectés des interprétations (LogDoctor, NetWatch) |
| Panneau d'opérations | Liste des tâches en cours, progression, annulation, historique des 20 dernières |

Une page cachée « Galerie de composants » (accessible en mode développeur) affiche chaque composant dans ses états, ce qui sert aussi de base aux captures de tests d'interface.

## 6. UX transverse

L'application doit se piloter aussi bien à la souris qu'au clavier, et rendre service même fenêtre fermée. Ces fonctions transverses passent avant les finitions de chaque module.

### Palette de commandes (Ctrl+K)

Un champ unique, ouvert depuis n'importe quelle page, qui combine actions et recherche globale :

- actions (« Scanner Téléchargements », « Tester la connexion », « Mettre ClipVault en pause », « Ouvrir les paramètres réseau ») ;
- résultats de recherche groupés par catégorie (section 13) ;
- correspondance approximative, accents ignorés, historique des commandes récentes en tête ;
- navigation clavier complète (flèches, Entrée, Échap, Tab pour changer de catégorie).

### Zone de notification

L'icône indique l'état global (normal, alerte réseau, ClipVault en pause). Son menu propose : Ouvrir, Capturer du texte, Historique du presse-papiers, Pause ClipVault (15 min, 1 h, jusqu'à réactivation), Test réseau rapide, Quitter. Fermer la fenêtre la réduit dans la zone de notification ; une bulle l'explique la première fois.

### Fenêtres rapides

- **ClipVault rapide** (Ctrl+Alt+H par défaut, Ctrl+Maj+V étant déjà le « collage sans mise en forme » de nombreuses applications) : petite fenêtre près du curseur avec recherche immédiate ; Entrée colle l'élément dans l'application active.
- **Résultat OCR** : panneau flottant après capture, avec texte modifiable, Copier, Enregistrer, Rechercher sur le Web (option désactivable).

### Notifications

Toasts Windows natifs pour les événements utiles uniquement : coupure réseau de plus de 30 s et retour, fin d'un scan long, mises à jour disponibles (au plus une fois par jour), erreur critique récente. Chaque type est réglable ; un mode « Ne pas déranger » suit l'Assistant de concentration de Windows. Le centre de notifications interne conserve 7 jours d'historique.

### Premier lancement

Un assistant en 4 écrans, chacun facultatif : bienvenue et principes de confidentialité ; vérification des composants (WinGet, Tesseract, langues OCR) avec liens officiels ; activation de ClipVault (désactivé tant que l'utilisateur ne l'a pas activé) ; choix des cartes du tableau de bord. L'outil de diagnostic d'installation reste accessible ensuite dans les paramètres.

### Rédaction de l'interface

- Verbes d'action précis sur les boutons (« Envoyer 12 fichiers à la Corbeille », pas « OK »).
- Erreurs en trois parties : ce qui s'est passé, pourquoi si connu, quoi faire.
- Vocabulaire constant, défini dans `docs/glossaire.md` (ex. toujours « Corbeille », jamais « poubelle »).
- Données techniques (chemins, ID d'événement, commandes) copiables d'un clic.

### Accessibilité

- Tout est atteignable au clavier, avec un ordre de tabulation logique et un focus visible (contour de 2 px `accent.primary`).
- Noms et descriptions accessibles renseignés sur chaque contrôle pour le Narrateur.
- Respect de la mise à l'échelle du texte Windows et des thèmes de contraste élevé (bascule sur la palette système).
- Zones cliquables d'au moins 32×32 px.

### Annuler plutôt que confirmer

Pour les actions réversibles (supprimer un élément ClipVault, désépingler, masquer une carte), l'action est immédiate et un bandeau propose « Annuler » pendant 8 secondes. Les confirmations sont réservées aux actions vraiment irréversibles ou coûteuses.

## 7. Module AppManager

AppManager inventorie tous les logiciels depuis plusieurs sources Windows, indique honnêtement lesquels WinGet sait gérer, et exécute installations, mises à jour et désinstallations une par une, avec la commande affichée avant chaque action.

### Inventaire

| Source | Méthode | Informations |
| --- | --- | --- |
| Programmes Win32 machine | Registre `HKLM\...\Uninstall` (vues 64 et 32 bits) | Nom, version, éditeur, date, taille estimée, chaîne de désinstallation |
| Programmes Win32 utilisateur | Registre `HKCU\...\Uninstall` | Idem |
| Applications MSIX / Store | `Get-AppxPackage` (PowerShell) | Nom, version, éditeur, famille de paquet |
| Correspondance WinGet | `Get-WinGetPackage` (module Microsoft.WinGet.Client) | Identifiant, source, version disponible |

Les entrées système (composants sans nom affichable, `SystemComponent=1`, mises à jour KB) sont masquées par défaut avec un filtre pour les afficher. Chaque logiciel porte une pastille « Géré par WinGet » ou « Non géré » ; aucune mise à jour n'est promise pour les seconds.

### Mises à jour

- Vérification à la demande et planifiée (par défaut une fois par jour, réseau requis).
- Tableau version installée → version proposée, lien vers les notes de version quand le manifeste en fournit.
- Sélection multiple et file d'attente : les opérations WinGet s'exécutent une à la fois, dans l'ordre choisi.
- Liste d'exclusion : ignorer un paquet ou une version précise (« ne plus me proposer la 24.1 »).
- Progression et sortie en direct dans un panneau dépliable ; journal conservé par opération.

### Installation

Recherche dans le catalogue via `Find-WinGetPackage`, fiche détaillée (éditeur, licence, page d'accueil, taille si connue), choix de la portée (utilisateur ou machine) quand le paquet le permet.

### Désinstallation

1. Si le logiciel est géré par WinGet : `Uninstall-WinGetPackage` en mode interactif.
2. Sinon : lancement de la chaîne `UninstallString` officielle, donc avec l'interface de l'éditeur. La variante silencieuse `QuietUninstallString` n'est jamais utilisée.
3. Avant le lancement : aperçu de la commande exacte, effet attendu, besoin d'élévation éventuel.
4. Après : nouvelle lecture de l'inventaire pour confirmer la disparition, ou signaler un échec.

### Gestion des codes de retour

Codes interprétés et affichés en français : succès, redémarrage requis (3010 et équivalents WinGet), annulé par l'utilisateur, paquet introuvable, conflit d'installation en cours, accès refusé. Un redémarrage requis déclenche un bandeau persistant jusqu'au redémarrage.

### Programmes au démarrage

| Emplacement | Lecture | Désactivation |
| --- | --- | --- |
| `HKCU\...\Run` | Oui | Oui, via la clé `StartupApproved` (réversible, comme le Gestionnaire des tâches) |
| `HKLM\...\Run` (32 et 64 bits) | Oui | Oui, via l'assistant élevé |
| Dossier Démarrage utilisateur | Oui | Oui, via `StartupApproved\StartupFolder` |
| Dossier Démarrage commun | Oui | Oui, via l'assistant élevé |
| Tâches planifiées à l'ouverture de session | Oui | Non en v1.0 (lecture seule) |

Pour chaque entrée : chemin de l'exécutable, existence du fichier, signature Authenticode (éditeur vérifié, non signé, signature invalide). Une entrée dont le fichier n'existe plus est signalée « orpheline ».

### Amélioration : sauvegarde de la liste des logiciels

Export de la liste des paquets WinGet en JSON (format `winget export`) et réimport guidé sur un PC neuf, avec sélection des paquets à réinstaller. Très utile pour reconstruire un poste.

### Diagnostic WinGet

Si WinGet ou le module PowerShell manque : message clair, version détectée, lien vers le Microsoft Store (App Installer) et vers la page officielle de WinGet, bouton « Installer le module PowerShell » qui affiche la commande `Install-Module Microsoft.WinGet.Client -Scope CurrentUser` avant exécution. L'inventaire du registre reste disponible sans WinGet.

## 8. Module NetWatch

NetWatch surveille la connexion en continu, localise chaque coupure (réseau local, au-delà du routeur, DNS) et produit un historique exportable, sans droits administrateur.

### Interfaces

Pour chaque interface (via `GetAdaptersAddresses` et psutil) : nom, type (Ethernet, Wi-Fi, VPN, virtuelle), état, vitesse du lien, adresses IPv4/IPv6, masque, passerelle, serveurs DNS, adresse MAC. Pour le Wi-Fi (API Native Wifi) : nom du réseau, qualité du signal, bande, canal. Les interfaces virtuelles (Hyper-V, WSL, VPN) sont identifiées et masquables.

### Surveillance continue

| Sonde | Méthode | Intervalle par défaut |
| --- | --- | --- |
| Passerelle | ICMP via `IcmpSendEcho2` (iphlpapi, sans admin), adresse lue dynamiquement | 5 s |
| Cibles Internet | ICMP vers une liste configurable (au moins 2 cibles, proposées à l'installation et modifiables) | 5 s |
| Repli TCP | Connexion TCP 443 vers une cible, si l'ICMP est filtré | Si ICMP échoue |
| DNS | Résolution d'un nom configurable via le résolveur système et via chaque serveur DNS déclaré (dnspython) | 30 s |

Mesures calculées par fenêtre glissante d'une minute : latence min/moyenne/max, gigue, perte en pourcentage. Toutes les sondes ont un timeout (2 s par défaut) et l'échantillonnage se suspend en veille ou sur batterie faible si l'option est activée.

### Détection et localisation des coupures

Une coupure commence après 3 échecs consécutifs et se termine après 2 succès. Sa localisation est une **hypothèse** affichée comme telle :

| Passerelle | Internet (IP) | DNS | Hypothèse affichée |
| --- | --- | --- | --- |
| Échec | Échec | Échec | Problème de réseau local (câble, Wi-Fi, routeur) |
| OK | Échec | Échec | Problème au-delà du routeur (box, fournisseur d'accès) |
| OK | OK | Échec | Problème de résolution DNS |
| OK | OK partiel | OK | Dégradation (pertes ou latence élevée) |

Chaque coupure enregistre début, fin, durée, sondes en échec et qualité Wi-Fi au même moment.

### Historique et graphiques

- Courbe de latence par cible avec bandes rouges sur les coupures et marqueurs de pertes ; zoom et sélection de plage (1 h, 24 h, 7 j, 30 j, personnalisée).
- Rétention : mesures brutes 7 jours, agrégats à la minute 90 jours, coupures 1 an (tous réglables).
- Export CSV (mesures, coupures) et **rapport de coupures** HTML imprimable, prêt à joindre à une réclamation auprès du fournisseur d'accès.

### Tests ponctuels

- Test de ports TCP sur une liste hôte:port saisie par l'utilisateur, avec timeout et résultat (ouvert, refusé, sans réponse).
- Résolution DNS d'un nom choisi, comparée entre serveurs.
- Traceroute (`tracert` avec arguments en liste, sortie interprétée) pour situer le saut fautif.

### Diagnostic guidé

Une suite d'étapes exécutée dans l'ordre, chacune affichant son résultat et sa conclusion : interface active → adresse IP valide (pas d'APIPA 169.254.x.x) → passerelle joignable → Internet joignable par IP → DNS fonctionnel → ports courants (80, 443). Le diagnostic s'arrête au premier échec, explique ce qu'il signifie et propose des vérifications manuelles, sans rien modifier sur le système.

### Découverte du réseau local

- Lancée uniquement par un clic explicite, sur un sous-réseau d'une interface locale, privé (RFC 1918) et au plus /22 (1 022 adresses).
- Méthode : requêtes ARP via `SendARP`, limitées à 20 par seconde, puis nom DNS inverse ; fabricant déduit du préfixe MAC à partir d'une base OUI locale.
- Résultats en trois états : a répondu, n'a pas répondu (« peut être présent mais silencieux »), erreur.
- Aucune adresse publique, aucun balayage de ports en masse, aucune tentative de contournement de pare-feu.

## 9. Module ScreenText

ScreenText capture une zone d'écran par raccourci global et en extrait le texte en local, avec deux moteurs au choix : Windows OCR (intégré, rien à installer) et Tesseract (plus de langues, plus de réglages). Aucune image ne quitte le PC.

### Capture

- Raccourci global par défaut **Ctrl+Alt+O**, modifiable ; si `RegisterHotKey` échoue (raccourci déjà pris), l'application le signale et propose un autre choix.
- Modes : zone rectangulaire, fenêtre sous le curseur, écran entier, répéter la dernière zone.
- Calque figé couvrant le bureau virtuel complet, correct en multi-écran et avec des mises à l'échelle DPI différentes ; loupe près du curseur et dimensions de la sélection affichées.
- Échap annule ; clic droit recommence la sélection.

### Reconnaissance

| Aspect | Windows OCR | Tesseract 5.x |
| --- | --- | --- |
| Installation | Aucune (langues des modules linguistiques Windows) | Programme + fichiers de langue `.traineddata` |
| Qualité sur texte d'écran | Bonne sans réglage | Bonne après prétraitement |
| Langues | Celles installées dans Windows | Plus de 100, téléchargeables |
| Mise en page | Lignes et mots | Blocs, paragraphes, mode tableau (TSV) |
| Rôle | Moteur par défaut s'il est disponible | Moteur alternatif ou principal, au choix |

Prétraitement avant Tesseract : agrandissement ×2 ou ×3 si le texte est petit, niveaux de gris, inversion automatique des thèmes sombres, seuillage adaptatif.

**Langue** : Tesseract ne détecte pas la langue, seulement l'écriture (latin, cyrillique, etc.) via son mode OSD. L'utilisateur choisit donc un jeu de langues (par défaut français + anglais) ; l'écriture détectée sert à proposer un autre jeu si le résultat semble incohérent.

### Résultat

- Panneau flottant avec aperçu de la capture, texte modifiable et indice de confiance par ligne (mots incertains soulignés).
- Mise en forme : fusion des lignes en paragraphes, suppression des césures de fin de ligne, espaces normalisés ; bascule « conserver la mise en page ».
- Éléments détectés cliquables : liens, adresses e-mail, numéros de téléphone.
- Actions : Copier, Copier sur une ligne, Exporter en TXT, Enregistrer dans l'historique.
- Amélioration : lecture des **codes QR et codes-barres** dans la zone capturée (bibliothèque zxing-cpp, Apache 2.0), utile pour un lien affiché à l'écran.

### Historique

- Enregistre le texte, la date, le moteur et la langue. Le titre de la fenêtre source et une miniature sont **désactivés par défaut** (données potentiellement sensibles).
- Contenu chiffré avec DPAPI, recherche plein texte via un index FTS5 construit en mémoire, jamais écrit sur disque.
- Suppression d'une entrée (annulable 8 s), effacement complet après confirmation, désactivation de l'historique, rétention par défaut de 90 jours.

### Composants et diagnostic

- Détection de Tesseract (chemin configuré, puis emplacements standard), version minimale 5.0, liste des langues installées.
- Si absent : explication, lien vers la page officielle du projet Tesseract et l'installateur Windows qu'elle recommande ; Windows OCR reste utilisable.
- Téléchargement facultatif des langues depuis le dépôt officiel `tesseract-ocr/tessdata_best` ou `tessdata_fast`, avec vérification de la taille et de l'empreinte, dans le dossier de données utilisateur (pas besoin d'admin).
- Une fois les composants installés, tout fonctionne hors ligne.

## 10. Module LogDoctor

LogDoctor transforme les journaux Windows en une chronologie lisible : il regroupe les erreurs répétées, les relie à ce qui a changé juste avant (mise à jour, installation, arrêt brutal) et propose des pistes tirées d'une base de fiches vérifiées, toujours séparées des faits.

### Collecte

- API `EvtQuery` / `EvtNext` / `EvtRender` (pywin32) avec filtres XPath côté système : période, niveau, fournisseur, identifiant d'événement. Les messages sont formatés par `EvtFormatMessage` avec un cache des métadonnées de fournisseur.
- Journaux lus par défaut : System, Application, Setup, et quelques journaux opérationnels utiles (Diagnostics-Performance pour les temps de démarrage, WindowsUpdateClient).
- Journal Security : uniquement via l'assistant élevé, sur demande, avec explication.
- Lecture paginée en tâche de fond, annulable ; un journal inaccessible est signalé avec la raison (accès refusé, journal désactivé, introuvable).
- Les journaux système ne sont jamais modifiés ni vidés. NexusDesk conserve sa propre copie des événements collectés (30 jours par défaut, taille plafonnée).

### Analyse

- **Regroupement** : signature = fournisseur + identifiant + message normalisé (nombres, GUID, chemins et adresses masqués). Pour chaque groupe : nombre d'occurrences, première et dernière date, tendance.
- **Chronologie des incidents** : événements d'erreur rapprochés (fenêtre de 2 minutes) regroupés en incidents, affichés sur une frise avec les marqueurs de contexte.
- **Marqueurs de contexte** : démarrages et arrêts (6005, 6006), arrêts inattendus (6008, Kernel-Power 41), mises à jour Windows installées, logiciels installés ou désinstallés (MsiInstaller), pilotes installés.
- **« Qu'est-ce qui a changé avant ? »** : pour un incident sélectionné, liste des changements des 48 heures précédentes. C'est une corrélation dans le temps, présentée comme une piste, pas comme une cause.
- **Top des erreurs** sur 24 h, 7 j et 30 j, et nombre d'arrêts inattendus.
- Amélioration : **indice de stabilité** lu depuis le Moniteur de fiabilité Windows (`Win32_ReliabilityStabilityMetrics`), affiché en courbe sur 30 jours.

### Base de fiches de diagnostic

Fichiers YAML dans `knowledge/`, relus à la main, versionnés avec l'application. Chaque fiche contient :

| Champ | Contenu |
| --- | --- |
| Correspondance | Fournisseur, identifiants, motif de message éventuel |
| Ce que l'événement indique | Fait, en une ou deux phrases |
| Gravité habituelle | Souvent bénin, à surveiller, important |
| Causes fréquentes | Hypothèses, ordonnées, chacune marquée « hypothèse » |
| Vérifications proposées | Étapes manuelles non destructives |
| Liens | Documentation officielle (learn.microsoft.com, support du fabricant) |

La v1.0 couvre au moins 40 événements fréquents, dont : Kernel-Power 41, EventLog 6008, BugCheck 1001, WHEA-Logger 17/18/19, disk 7/51/153, Ntfs 55/98, Application Error 1000, Application Hang 1002, .NET Runtime 1026, Service Control Manager 7000/7001/7009/7031/7034, DNS Client 1014, Schannel 36887, DistributedCOM 10016 (marqué « souvent bénin », pour éviter l'inquiétude inutile).

Un événement sans fiche s'affiche avec ses seules données brutes et la mention « Aucune piste documentée pour cet événement ». Aucun texte de diagnostic n'est généré à la volée.

### Affichage

Chaque fiche d'événement présente deux blocs visuellement distincts : **Faits collectés** (date, journal, fournisseur, identifiant, niveau, message, données XML) et **Pistes de diagnostic** (pastille Hypothèse). Les limites sont rappelées : journaux tronqués par leur taille maximale, événements effacés, fournisseur sans message traduit.

### Actions de réparation

Propositions documentées seulement, jamais automatiques : `sfc /scannow`, `DISM /Online /Cleanup-Image /RestoreHealth`, `chkdsk C: /scan` (analyse en ligne, sans réparation). Pour chacune : ce qu'elle fait, durée typique, besoin d'admin, aperçu de la commande. Exécution séparée, après confirmation, via l'assistant élevé, sortie affichée en direct.

### Export

CSV et JSON des événements filtrés ; rapport HTML d'un incident (chronologie, faits, pistes, liens) pour le partager avec un technicien.

## 11. Module DiskPilot

DiskPilot montre où part l'espace disque (carte proportionnelle, catégories, gros fichiers, doublons) et permet de libérer de la place en envoyant les fichiers choisis à la Corbeille, jamais automatiquement et jamais pour un fichier système.

### Volumes

Pour chaque volume : lettre, nom, système de fichiers, type (fixe, amovible, réseau), espace total, utilisé et libre, avec une jauge colorée (avertissement sous 15 %, alerte sous 5 %, seuils réglables). Un volume réseau lent est signalé avant scan.

### Scan

- Parcours itératif avec `os.scandir` (les attributs sont fournis sans appel supplémentaire sous Windows), en tâche de fond, annulable, progression par nombre de fichiers et dossier en cours.
- Deux tailles calculées : taille logique et **taille sur disque** (`GetCompressedFileSizeW`, qui tient compte de la compression NTFS et des fichiers creux).
- **Liens physiques** comptés une seule fois grâce à l'identifiant de fichier, pour ne pas gonfler les totaux.
- **Jonctions et liens symboliques** : jamais suivis par défaut, listés à part avec leur cible ; politique modifiable par dossier.
- **Fichiers OneDrive à la demande** (attributs `RECALL_ON_DATA_ACCESS` / `RECALL_ON_OPEN`) : comptés avec leur taille sur disque réelle, jamais lus ni hachés, pour ne déclencher aucun téléchargement.
- Fichiers inaccessibles ignorés proprement et listés dans un onglet « Erreurs » avec la raison (accès refusé, chemin trop long, fichier verrouillé).
- Objectif de performance : 1 million de fichiers en moins de 3 minutes sur SSD NVMe, interface fluide pendant le scan.

### Exclusions par défaut

`C:\Windows`, `C:\Program Files`, `C:\Program Files (x86)`, `C:\ProgramData`, `$Recycle.Bin`, `System Volume Information`, `Recovery`, ainsi que `pagefile.sys`, `hiberfil.sys` et `swapfile.sys` (affichés comme fichiers système, jamais supprimables). L'utilisateur peut scanner un dossier exclu en lecture seule, avec un avertissement.

### Visualisation

- **Carte proportionnelle (treemap)** des dossiers et fichiers, navigable par double-clic, colorée par catégorie. C'est la vue la plus utile pour comprendre un disque en quelques secondes.
- Arborescence triée par taille avec pourcentage du parent.
- Répartition par catégorie : vidéos, images, audio, documents, archives, installateurs, code et projets, autres.
- Liste des plus gros fichiers, filtrable par extension, taille, date de modification.

### Doublons

1. Regroupement par taille exacte (taille minimale réglable, 1 Mo par défaut).
2. Empreinte partielle SHA-256 (premiers et derniers 64 Ko) pour éliminer vite les faux candidats.
3. Empreinte SHA-256 complète pour confirmer.
4. Résultat par groupe : fichiers identiques, espace récupérable, suggestion de l'exemplaire à garder (le plus ancien, ou celui hors de Téléchargements), toujours modifiable.

Les empreintes sont mises en cache par (chemin, taille, date de modification) pour accélérer les scans suivants.

### Changements pendant le scan

Taille et date de modification sont relevées au scan, puis vérifiées à nouveau juste avant toute suppression. Un fichier modifié, déplacé ou disparu est retiré de la sélection et signalé.

### Suppression

- Envoi à la **Corbeille** par défaut via `IFileOperation`, donc récupérable. La suppression définitive est désactivée par défaut et exige, si activée, une confirmation saisie.
- Avant toute suppression : liste détaillée des éléments, total en nombre et en taille, aperçu (miniature d'image, premières lignes d'un texte, métadonnées), bouton « Afficher dans l'Explorateur ».
- Refus systématique pour : fichiers avec l'attribut système, chemins exclus, fichiers en cours d'utilisation, contenu des dossiers protégés.
- Rapport après opération : réussis, échoués avec raison, espace réellement libéré.

### Suggestions de nettoyage

Pistes présentées comme des suggestions à vérifier, jamais comme des fichiers « inutiles » : installateurs (.exe, .msi) de plus de 90 jours dans Téléchargements, fichiers de %TEMP% de plus de 7 jours non verrouillés, doublons, gros fichiers non modifiés depuis un an. Pour le nettoyage système (mises à jour, cache de Windows), un bouton ouvre l'outil officiel « Assistant Stockage » de Windows plutôt que de le réimplémenter.

### Conservation et export

Sont conservés : le résumé des 5 derniers scans par dossier, les 1 000 plus gros fichiers et les dossiers jusqu'à 4 niveaux. Ces chemins alimentent la recherche globale. Export CSV (fichiers, dossiers, doublons) et comparaison entre deux scans d'un même dossier (« ce dossier a pris 12 Go depuis le mois dernier »).

## 12. Module ClipVault

ClipVault conserve l'historique texte du presse-papiers, chiffré et à durée limitée, et ne s'active qu'avec l'accord explicite de l'utilisateur. Il respecte les signaux d'exclusion posés par les gestionnaires de mots de passe, sans jamais garantir qu'un secret sera toujours reconnu.

### Capture

- **Désactivé par défaut**, activé lors du premier lancement ou dans les paramètres, après un écran qui explique ce qui est enregistré.
- Écoute par `AddClipboardFormatListener` (message `WM_CLIPBOARDUPDATE`), sans interrogation périodique.
- Texte uniquement (`CF_UNICODETEXT`), 1 Mo maximum par élément ; aucune image, aucun fichier en v1.0.
- Les copies faites par NexusDesk lui-même ne sont pas recapturées.
- État visible en permanence : icône de zone de notification (active, en pause, désactivée) et bandeau dans le module.

### Exclusions

| Mécanisme | Fiabilité | Comportement |
| --- | --- | --- |
| Format `ExcludeClipboardContentFromMonitorProcessing` | Élevée (posé volontairement par l'application source) | Jamais capturé |
| Format `CanIncludeInClipboardHistory` à 0 | Élevée | Jamais capturé |
| Format `Clipboard Viewer Ignore` | Élevée | Jamais capturé |
| Liste d'applications exclues (nom de processus) | Moyenne : l'application source se déduit de `GetClipboardOwner` ou, à défaut, de la fenêtre active | Jamais capturé ; liste préremplie avec KeePass, KeePassXC, Bitwarden, 1Password |
| Détection de secrets probables (clés privées, jetons d'API connus, JWT, chaîne sans espace à forte entropie) | Faible à moyenne, faux positifs et négatifs possibles | Non enregistré, notification discrète « Élément ignoré : secret probable » avec « Conserver quand même » |

Les limites sont documentées dans l'interface et dans `docs/confidentialite.md` : une application qui ne pose aucun signal et un secret sans motif reconnaissable seront capturés.

### Organisation

- Doublons : un texte déjà présent remonte en tête au lieu d'être dupliqué ; compteur d'utilisations.
- **Épinglés** : restent en tête et ne sont jamais purgés par la rétention.
- **Collections** (favoris) : groupes nommés, par exemple « Adresses », « Réponses client ».
- **Modèles** avec variables : `{date}`, `{heure}`, `{presse-papiers}` et champs à remplir à l'insertion (`{nom}`), saisis dans une petite fenêtre avant collage.
- Recherche instantanée plein texte, filtres par date, application source, collection.

### Utilisation

- Fenêtre rapide Ctrl+Alt+H : recherche, flèches, Entrée pour coller dans l'application précédente (option de collage automatique via `SendInput`, sinon simple copie).
- Amélioration : **transformations au collage** : texte brut, majuscules, minuscules, casse de titre, suppression des espaces superflus, une ligne, décodage d'URL.
- Copier, modifier, épingler, supprimer (annulable 8 s) depuis le module ou le menu contextuel.

### Rétention et effacement

- Par défaut : 7 jours et 500 éléments maximum hors épinglés (les deux réglables) ; purge automatique au démarrage puis toutes les heures.
- Pause depuis la zone de notification : 15 min, 1 h, jusqu'à réactivation.
- Effacement rapide de l'historique (hors épinglés ou tout) depuis la zone de notification, avec confirmation.
- Options : effacer à la fermeture de session ; ne rien capturer quand la session est verrouillée.

### Protection des données

Chaque élément est chiffré avec DPAPI (portée utilisateur courant) avant écriture ; l'index de recherche est construit en mémoire au démarrage et jamais écrit sur disque. Le contenu n'apparaît jamais dans les journaux techniques : un filtre de journalisation le garantit et un test automatisé le vérifie.

## 13. Tableau de bord et recherche globale

Le tableau de bord répond en un coup d'œil à « mon PC va-t-il bien ? » avec des données réelles et datées ; la recherche globale retrouve n'importe quelle donnée déjà collectée en moins de 100 ms, sans rescanner le disque.

### Bandeau « Santé du PC »

Une ligne de synthèse en haut, construite uniquement à partir de faits collectés, par exemple : « Réseau stable depuis 3 jours · C: 18 % libre · 4 mises à jour disponibles · 1 arrêt inattendu cette semaine ». Chaque segment est cliquable et ouvre le détail.

### Cartes

| Carte | Contenu | Source | Rafraîchissement |
| --- | --- | --- | --- |
| Réseau | État des interfaces, latence actuelle, mini-courbe 1 h, coupures sur 24 h | NetWatch | 5 s |
| Stockage | Jauge par volume, espace libre, tendance sur 30 jours | DiskPilot | 5 min |
| Logiciels | Nombre de mises à jour disponibles, date de vérification | AppManager | À chaque vérification |
| Erreurs Windows | Erreurs critiques et arrêts inattendus sur 7 jours, indice de stabilité | LogDoctor | 15 min |
| Captures de texte | 3 dernières captures (extrait), bouton Capturer | ScreenText | À chaque capture |
| Presse-papiers | Nombre d'éléments, état (actif, en pause, désactivé) ; aucun contenu affiché | ClipVault | Temps réel |
| Opérations | Tâches en cours avec progression | Gestionnaire de tâches | Temps réel |

Règles : chaque carte ouvre son module ; chaque valeur porte l'heure de sa collecte ; une collecte en échec affiche « Indisponible » avec la raison et un bouton Réessayer, jamais une valeur par défaut. Les cartes se masquent, se réordonnent par glisser-déposer et existent en deux tailles.

### Recherche globale

Accessible par la palette de commandes (Ctrl+K) et le champ de la barre supérieure.

| Catégorie | Données interrogées | Index |
| --- | --- | --- |
| Applications | Inventaire AppManager | FTS5 sur disque |
| Événements | Événements déjà collectés par LogDoctor | FTS5 sur disque |
| Fichiers | Chemins conservés des scans terminés | FTS5 sur disque |
| Textes OCR | Historique ScreenText | FTS5 **en mémoire**, reconstruit au démarrage |
| Presse-papiers | Historique ClipVault | FTS5 **en mémoire**, reconstruit au démarrage |
| Actions | Commandes de l'application | Liste statique |

Les contenus chiffrés (OCR, presse-papiers) ne sont jamais indexés sur disque : leur index est construit en mémoire à partir des données déchiffrées, ce qui évite qu'un index en clair contredise le chiffrement.

Comportement : saisie temporisée de 150 ms, accents et casse ignorés, préfixes acceptés, 5 résultats par catégorie avec « Tout voir », action principale par résultat (ouvrir dans le module, copier, afficher dans l'Explorateur). Les résultats ClipVault peuvent être exclus de la recherche globale par un réglage, et disparaissent quand le module est désactivé.

## 14. Données, stockage et confidentialité

Toutes les données vivent dans `%LOCALAPPDATA%\NexusDesk`, réparties entre deux bases SQLite, avec une rétention par type, un plafond de taille, des sauvegardes automatiques et un chiffrement DPAPI pour les contenus personnels.

### Emplacements

```
%LOCALAPPDATA%\NexusDesk\
  data\nexusdesk.db     paramètres, inventaires, événements, OCR, presse-papiers, scans
  data\metrics.db      mesures réseau brutes (écritures fréquentes, isolées)
  backups\             sauvegardes automatiques et pré-migration
  logs\                journaux techniques (rotation)
  tessdata\            langues Tesseract téléchargées
  cache\               miniatures, empreintes de fichiers
```

Le dossier local (et non itinérant) est retenu car les données décrivent cette machine. Un mode portable stocke tout à côté de l'exécutable si un fichier `portable.flag` y est présent.

### Réglages SQLite

Mode WAL, `foreign_keys=ON`, `busy_timeout=5000`, `synchronous=NORMAL`, requêtes exclusivement paramétrées via SQLAlchemy, une transaction par opération métier, file d'écriture unique. Erreurs de stockage (disque plein, base verrouillée, corruption) traduites en messages compréhensibles avec action proposée.

### Rétention par défaut

| Donnée | Durée | Plafond | Chiffrée |
| --- | --- | --- | --- |
| Mesures réseau brutes | 7 jours | — | Non |
| Agrégats réseau à la minute | 90 jours | — | Non |
| Coupures réseau | 1 an | — | Non |
| Événements Windows collectés | 30 jours | 100 000 événements | Non |
| Historique OCR | 90 jours | 5 000 entrées | Oui (DPAPI) |
| Presse-papiers (hors épinglés) | 7 jours | 500 éléments | Oui (DPAPI) |
| Résultats de scans | 5 derniers par dossier | 1 000 fichiers par scan | Non |
| Journal des opérations (installations, suppressions) | 1 an | — | Non |
| Journaux techniques | — | 5 fichiers × 5 Mo | Non (sans contenu personnel) |

Taille maximale des bases réglable (500 Mo par défaut) : au-delà, les données les plus anciennes sont purgées selon la politique de chaque type et une notification l'indique. Un `VACUUM` incrémental tourne chaque semaine.

### Migrations

1. Au démarrage, Alembic compare la version de la base à celle attendue.
2. Si une migration est nécessaire : sauvegarde cohérente via l'API `backup` de SQLite vers `backups\pre-migration-<version>-<date>.db`, puis `PRAGMA integrity_check` sur la copie.
3. Migration dans une transaction.
4. En cas d'échec : restauration automatique de la copie, message clair, journal détaillé ; l'application démarre en lecture seule plutôt que de perdre des données.

### Sauvegardes

Sauvegarde automatique quotidienne (7 conservées), sauvegarde et restauration manuelles depuis les paramètres, export des paramètres en JSON pour les transférer sur un autre PC. Restaurer une sauvegarde exige un redémarrage de l'application, annoncé avant.

### Confidentialité

- Aucune donnée envoyée hors du PC, aucune télémétrie, aucun rapport de plantage transmis ; les plantages produisent un rapport local que l'utilisateur peut consulter et partager lui-même.
- Journaux techniques : jamais de contenu du presse-papiers ni de texte OCR ; le chemin du profil est remplacé par `%USERPROFILE%`.
- Page « Mes données » dans les paramètres : volume occupé par type, export complet (JSON/CSV), effacement par type ou total.
- Les données chiffrées par DPAPI ne sont lisibles que par le même utilisateur Windows sur le même PC ; une sauvegarde restaurée sur un autre PC perd donc l'historique OCR et presse-papiers. Ce point est expliqué dans l'interface.

## 15. Paramètres

Les paramètres sont regroupés par onglet, validés par des schémas pydantic, appliqués sans redémarrage sauf mention contraire, et chaque onglet a son bouton « Rétablir les valeurs par défaut ». Une recherche filtre les réglages par mot-clé.

| Onglet | Réglages |
| --- | --- |
| Général | Lancement au démarrage de Windows (désactivé par défaut), comportement de la croix (réduire ou quitter), page d'accueil, mode développeur |
| Apparence | Thème (sombre, clair, suivre Windows), effet Mica, densité (confortable, compacte), taille du texte, animations |
| Raccourcis | Capture OCR, ClipVault rapide, palette de commandes, raccourcis de navigation ; détection des conflits ; réinitialisation |
| Notifications | Activation par type, seuils (durée de coupure, espace libre), Ne pas déranger, historique interne |
| Tableau de bord | Cartes visibles, ordre, tailles |
| AppManager | Fréquence de vérification, portée d'installation par défaut, liste d'exclusion des mises à jour, diagnostic WinGet |
| NetWatch | Cibles de surveillance, intervalles, timeouts, seuils de latence et de perte, nom DNS de test, ports à tester, pause sur batterie |
| ScreenText | Moteur par défaut, chemin de Tesseract, langues, prétraitement, historique (actif, durée, miniatures, titre de fenêtre) |
| LogDoctor | Journaux lus, profondeur de collecte, rétention, fréquence |
| DiskPilot | Exclusions, politique des liens et jonctions, taille minimale des doublons, suppression définitive (désactivée), seuils d'alerte d'espace |
| ClipVault | Activation, rétention, plafond, applications exclues, détection de secrets probables, collage automatique, effacement à la fermeture de session, visibilité dans la recherche globale |
| Données | Emplacement (lecture seule), taille maximale, rétention par type, sauvegardes, restauration, export, « Mes données », effacement |
| Diagnostic | Outil de diagnostic d'installation, ouverture du dossier des journaux, génération d'un rapport de diagnostic local |
| À propos | Version, notes de version, licences des composants tiers, vérification des mises à jour de NexusDesk |

### Outil de diagnostic d'installation

Un écran qui vérifie et affiche, avec un statut par ligne et une action corrective : version de Windows, présence et version de WinGet et du module PowerShell, présence et version de Tesseract et des langues, langues Windows OCR disponibles, droits d'écriture sur le dossier de données, intégrité des bases, raccourcis enregistrés, état de l'écoute du presse-papiers. Le résultat est exportable en texte, sans donnée personnelle, pour une demande d'aide.

## 16. Sécurité et fiabilité

Les règles ci-dessous s'appliquent à tous les modules et sont vérifiées par des tests ou par la revue de code ; aucune n'est optionnelle.

### Exécution de commandes

- Aucun `shell=True`, aucune chaîne de commande construite par concaténation : arguments en liste uniquement.
- Exécutables appelés par chemin absolu résolu et vérifié (existence, emplacement attendu, signature Microsoft pour `powershell.exe` et `winget.exe`).
- PowerShell lancé avec `-NoProfile -NonInteractive -Command` et un script figé dans le code ; les valeurs (identifiant de paquet, version) sont passées en paramètres et validées par expression régulière, jamais interpolées dans le script.
- Timeout sur chaque sous-processus, arrêt de l'arbre de processus en cas d'annulation.
- Aucune commande arbitraire saisissable par l'utilisateur dans l'interface.

### Assistant élevé

- Liste fermée de commandes, chacune avec un schéma de paramètres strict.
- Canal nommé à ACL limitée au SID de l'utilisateur, jeton à usage unique, vérification du PID parent.
- Journal de chaque commande exécutée (sans données personnelles), arrêt après 60 s d'inactivité.
- Aucune désactivation de protection Windows (Defender, UAC, pare-feu, SmartScreen), aucune modification de stratégie système.

### Entrées et données

- Validation de toutes les entrées (pydantic) : chemins normalisés et résolus, adresses IP et sous-réseaux via `ipaddress`, ports 1 à 65535, noms de domaine.
- Chemins longs (plus de 260 caractères) gérés avec le préfixe `\\?\`.
- Fichiers verrouillés et accès refusés traités comme des cas normaux, jamais comme des plantages.

### Robustesse

- Gestionnaire global d'exceptions : erreur journalisée, message compréhensible à l'utilisateur, application maintenue en vie quand c'est possible.
- Rapport de plantage local (pile d'appels sans données personnelles) proposé au redémarrage suivant.
- Mise en veille et reprise gérées : la surveillance réseau ignore l'intervalle de veille au lieu de le compter comme coupure.
- Arrêt propre : tâches annulées, bases fermées, écritures en attente terminées en moins de 3 s.
- Déduplication des tâches pour empêcher deux scans identiques simultanés.

### Chaîne d'approvisionnement

- Dépendances verrouillées avec empreintes (`uv.lock`), audit de vulnérabilités (`pip-audit`) dans le script de vérification.
- Inventaire des licences généré (`pip-licenses`) et affiché dans « À propos ».
- Téléchargements (langues Tesseract, base OUI) uniquement en HTTPS depuis les sources officielles, avec vérification de taille et d'empreinte quand elle est publiée.

## 17. Qualité et tests

Chaque lot est terminé seulement quand ses tests passent, que Ruff et mypy --strict ne signalent rien et que la couverture des services atteint 85 %. Les API Windows et le réseau sont simulés dans les tests unitaires ; les tests d'intégration tournent sur un vrai Windows.

### Niveaux de tests

| Niveau | Outils | Portée | Où |
| --- | --- | --- | --- |
| Unitaires | pytest, faux objets via `Protocol` | Services, dépôts, parseurs, règles métier | Partout (CI, Linux possible) |
| Propriétés | hypothesis | Normalisation des messages, parsing, calcul de tailles, détection de secrets | Partout |
| Interface | pytest-qt | Navigation, états vides et d'erreur, confirmations, palette, raccourcis internes | Windows |
| Intégration | pytest marqué `windows` | Registre, journaux, presse-papiers, ICMP local, DPAPI, Corbeille, Tesseract, Windows OCR | Windows uniquement |
| Bout en bout | Scénarios scriptés sur l'exécutable empaqueté | Démarrage, capture OCR, scan, export | Windows propre (machine virtuelle ou Windows Sandbox) |

### Cas obligatoires

- Persistance : transactions, contraintes, file d'écriture, erreurs disque plein et base verrouillée.
- Migrations : base vide, montée depuis chaque version, échec simulé avec restauration de la sauvegarde.
- Filtres, tri et recherche : accents, casse, préfixes, résultats par catégorie, exclusions de confidentialité.
- Réseau : latence, pertes, gigue, timeouts, échecs DNS (NXDOMAIN, timeout, serveur injoignable), classification des coupures, veille ignorée.
- OCR : images de référence générées (texte synthétique, thèmes clair et sombre, petites polices) avec taux de caractères corrects minimal ; Tesseract absent ; langue manquante.
- Journaux : accès refusé, journal vide, fournisseur sans message, regroupement et normalisation, correspondance des fiches.
- Disque : arborescences synthétiques (liens physiques, jonctions, fichiers creux, attributs cloud simulés, chemins longs, fichiers verrouillés), tailles, doublons, exclusions, fichier modifié avant suppression.
- Presse-papiers : formats d'exclusion, applications exclues, doublons, rétention, pause, absence de contenu dans les journaux.
- Rétention, exports CSV/JSON, sauvegardes et restauration.
- Annulation de chaque tâche longue et déduplication.
- Dépendances manquantes : WinGet, module PowerShell, Tesseract, langues Windows OCR.
- Assistant élevé : commande hors liste refusée, jeton invalide refusé, paramètres invalides refusés.

### Règles

- Aucune donnée personnelle dans les tests ni les fixtures ; données générées ou anonymisées.
- Une anomalie corrigée entraîne un test de non-régression.
- Règles de dépendance entre couches vérifiées par import-linter.
- Hooks pre-commit : Ruff (lint et format), mypy, tests rapides.
- Les résultats réels sont reportés tels quels dans le rapport de validation ; un test non lancé est indiqué « non exécuté », jamais « réussi ».

## 18. Packaging, distribution et mises à jour

NexusDesk est livré sous forme d'installateur par utilisateur (sans admin) et d'archive portable, construits par un script PowerShell unique et testés sur un Windows vierge. Tesseract n'est pas embarqué : Windows OCR suffit au démarrage.

### Scripts PowerShell (`scripts/`)

| Script | Rôle |
| --- | --- |
| `install-dev.ps1` | Vérifie Windows et Python 3.12, installe uv si absent, crée l'environnement depuis `uv.lock`, installe les hooks pre-commit |
| `run.ps1` | Lance l'application depuis les sources (option `-Dev` pour le mode développeur) |
| `test.ps1` | Tests unitaires ; `-Integration` pour les tests Windows ; `-Coverage` pour le rapport |
| `check.ps1` | Ruff, mypy --strict, import-linter, pip-audit, inventaire des licences |
| `build.ps1` | Version, PyInstaller (mode dossier), installateur Inno Setup, archive portable, empreintes SHA-256 |
| `smoke-test.ps1` | Démarre l'exécutable empaqueté, vérifie ressources, chemins, base, puis le ferme proprement |

### Exécutable

- PyInstaller en **mode dossier** (démarrage plus rapide et moins de faux positifs antivirus que le fichier unique).
- Modules Qt inutiles exclus (WebEngine, 3D, Multimedia, Charts, etc.) ; objectif inférieur à 150 Mo installé.
- Informations de version Windows (éditeur, version, description) intégrées à l'exécutable.
- Ressources (icônes, QSS, fiches de diagnostic, migrations) chargées via un résolveur de chemins unique, compatible sources et version empaquetée.

### Installateur (Inno Setup)

- Installation par utilisateur dans `%LOCALAPPDATA%\Programs\NexusDesk`, sans élévation.
- Raccourci du menu Démarrer ; démarrage avec Windows proposé, décoché par défaut.
- Mise à jour par-dessus une version existante en préservant données et paramètres ; l'application en cours est fermée proprement avant.
- Désinstallation : données conservées par défaut, case « Supprimer aussi mes données » décochée ; entrées de démarrage et raccourcis retirés.

### Mises à jour de NexusDesk

- Vérification manuelle par défaut ; vérification hebdomadaire automatique proposée (requête HTTPS vers la page des versions du projet, rien d'autre n'est envoyé).
- Téléchargement de l'installateur, vérification de l'empreinte SHA-256 publiée et de la signature si présente, installation seulement après accord.
- Notes de version affichées avant l'installation.

### Signature de code

Un exécutable non signé déclenche l'avertissement SmartScreen. Options sans coût : rester non signé avec une explication dans le README, ou demander une signature gratuite pour projet libre (programme SignPath Foundation, si le projet est publié en open source). Option à terme : publier NexusDesk dans le dépôt WinGet communautaire.

### Validation de l'empaquetage

Installation, premier lancement, fonctions principales, mise à jour et désinstallation testés dans Windows Sandbox (environnement vierge, sans Python), résultats consignés dans le rapport de validation.

## 19. Plan de livraison par lots

Le développement avance en 9 lots ; chacun produit une version installable et utilisable (0.1 à 0.9), et la v1.0 suit le lot de finitions. Ordre retenu : du plus testable au plus dépendant d'outils externes. Durée totale estimée : 19 à 24 semaines à temps plein pour un développeur expérimenté.

| Lot | Version | Contenu | Critère de sortie | Durée estimée |
| --- | --- | --- | --- | --- |
| 0. Socle | 0.1 | uv, structure, configuration, bases + Alembic, gestionnaire de tâches, journalisation, instance unique, zone de notification, fenêtre et navigation, design system, paramètres de base, diagnostic d'installation, scripts | L'exécutable empaqueté démarre, se réduit, se rouvre ; migrations et sauvegardes testées | 3 semaines |
| 1. DiskPilot | 0.2 | Volumes, scan, treemap, doublons, suppression vers la Corbeille, export | Scan d'1 million de fichiers sans gel, tests de liens et fichiers cloud verts | 3 semaines |
| 2. NetWatch | 0.3 | Interfaces, sondes, coupures, graphiques, diagnostic guidé, tests de ports, découverte locale, export | 24 h de surveillance sans fuite mémoire, classification des coupures testée | 2 à 3 semaines |
| 3. Tableau de bord et recherche | 0.4 | Cartes, bandeau santé, palette de commandes, recherche FTS5 | Toutes les cartes alimentées par des données réelles ou « Indisponible » | 1 à 2 semaines |
| 4. ClipVault | 0.5 | Écoute, exclusions, chiffrement, fenêtre rapide, modèles, transformations, rétention | Tests de formats d'exclusion et d'absence de contenu dans les journaux verts | 2 semaines |
| 5. ScreenText | 0.6 | Capture multi-écran, Windows OCR, Tesseract, résultat, historique, QR codes | Taux de caractères corrects ≥ 95 % sur le jeu d'images de référence | 2 semaines |
| 6. LogDoctor | 0.7 | Collecte, regroupement, chronologie, contexte, 40 fiches, exports | Fiches relues, faits et hypothèses séparés dans toutes les vues | 3 semaines |
| 7. AppManager et assistant élevé | 0.8 | Inventaire, WinGet, file d'opérations, démarrage, export de la liste ; assistant élevé (puis journal Security dans LogDoctor) | Installation, mise à jour, désinstallation testées sur Windows Sandbox | 3 semaines |
| 8. Finitions | 0.9 — 1.0 | Accessibilité, performance, onboarding, installateur, mises à jour, documentation, rapport de validation | Tous les critères de la section 20 remplis | 2 à 3 semaines |

Après chaque lot : tests et vérifications lancés, anomalies corrigées, documentation à jour, liste des fonctions réellement terminées et des limites restantes ajoutée à `docs/journal-des-lots.md`.

## 20. Livrables et critères d'acceptation

La v1.0 est acceptée quand tous les livrables existent et que chaque critère ci-dessous est vérifié et consigné dans le rapport de validation, avec la date et le résultat réel.

### Livrables

- Code source complet, architecture en couches conforme à la section 4.
- Tests automatisés (unitaires, interface, intégration Windows) et rapport de couverture.
- `pyproject.toml`, `uv.lock`, scripts PowerShell de la section 18.
- Installateur, archive portable et empreintes SHA-256.
- Documentation en français : `README.md`, guide d'utilisation, architecture et ADR, permissions requises, confidentialité, dépendances et licences, procédures d'installation, de mise à jour, de sauvegarde, de restauration et de désinstallation, installation de Tesseract.
- Rapport de validation et liste des limitations connues.

### Critères d'acceptation

- [ ] Aucun bouton sans action ; aucune fonction simulée.
- [ ] Toutes les fonctions courantes marchent en utilisateur standard ; chaque élévation affiche son motif.
- [ ] L'interface ne se fige jamais plus de 100 ms pendant un scan, une capture OCR, une lecture de journaux ou une opération WinGet.
- [ ] Toute tâche longue est annulable et deux tâches identiques ne peuvent pas tourner en même temps.
- [ ] Aucune valeur inventée : chaque donnée affichée est datée ou marquée « Indisponible ».
- [ ] Aucune suppression sans aperçu et confirmation ; suppression vers la Corbeille par défaut.
- [ ] ClipVault désactivé par défaut ; aucun contenu du presse-papiers ni texte OCR dans les journaux techniques (vérifié par test).
- [ ] Aucune connexion réseau sortante en dehors des fonctions qui l'annoncent (vérifié par capture réseau pendant 24 h d'usage).
- [ ] Ruff et mypy --strict sans erreur ; couverture des services ≥ 85 %.
- [ ] Exécutable testé sur Windows Sandbox sans Python : installation, usage, mise à jour, désinstallation avec données conservées.
- [ ] Empreinte mémoire et temps de démarrage conformes à la section 2.
- [ ] Navigation clavier complète et compatibilité Narrateur vérifiées sur chaque page.

## 21. Consignes pour l'agent de développement

Si ce cahier des charges est confié à un agent IA, il travaille un lot à la fois, dans le dossier du projet, et rend compte honnêtement de ce qui a été exécuté et vérifié.

1. **Inspecter d'abord** : version de Windows, Python, uv, Git, PowerShell, WinGet, Tesseract, contenu du dossier. Ne supprimer, déplacer ni écraser aucun fichier existant sans autorisation.
2. **Un lot par session** : annoncer le lot, son plan court, puis le réaliser. Ne pas commencer le lot suivant sans avoir rempli le critère de sortie du lot en cours.
3. **Choix réversibles** : décider seul et consigner la décision dans un ADR. Choix irréversibles ou contraires à ce cahier : demander d'abord.
4. **Environnement** : si l'agent ne tourne pas sous Windows (conteneur Linux, par exemple), il le dit, écrit et lance les tests portables, et marque les tests Windows et l'empaquetage comme « à exécuter sur Windows ». Il ne prétend jamais les avoir lancés.
5. **Commits** : petits, un sujet par commit, messages en français à l'impératif ; branche par lot.
6. **Fin de lot** : lancer `check.ps1` et `test.ps1` (ou leurs équivalents), corriger, mettre à jour la documentation, puis livrer un compte rendu en quatre parties : terminé et vérifié, terminé non vérifié (et pourquoi), non fait, limites découvertes.
7. **Interdits** : bouton sans action, données factices affichées comme réelles, `shell=True`, contournement d'une protection Windows, contenu personnel dans les journaux ou les tests, dépendance ajoutée sans justification dans `docs/dependances.md`.

**Première action** : inspecter l'environnement et le dossier, présenter le plan du lot 0, puis démarrer le socle technique.

## 22. Limitations connues et questions ouvertes

Ces limites sont assumées pour la v1.0 et doivent apparaître dans la documentation utilisateur ; les questions ouvertes sont à trancher avant ou pendant le lot indiqué.

### Limitations connues

- WinGet ne gère pas tous les logiciels installés ; ceux qu'il ignore n'ont pas de mise à jour proposée.
- La détection des secrets dans ClipVault repose sur des signaux posés par les applications et sur des motifs ; elle ne peut pas tout reconnaître.
- L'application source d'une copie est parfois déduite de la fenêtre active, donc approximative.
- La localisation des coupures réseau est une hypothèse fondée sur trois sondes, pas un diagnostic certain.
- Un appareil qui ne répond pas à l'ARP peut être présent sur le réseau.
- La qualité de l'OCR dépend de la taille du texte, du contraste et des langues installées.
- Le scan Python reste plus lent qu'un outil lisant directement la table NTFS (qui exigerait l'admin).
- Les historiques chiffrés par DPAPI ne sont pas transférables vers un autre PC ou un autre compte.
- Les tâches planifiées au démarrage sont visibles mais non modifiables en v1.0.
- Sans signature de code, SmartScreen avertit au premier lancement de l'installateur.

### Questions ouvertes

- [ ] Publier le projet en open source ? Conditionne la signature gratuite et la publication dans WinGet (avant le lot 8).
- [ ] Liste définitive des cibles Internet proposées par défaut dans NetWatch (lot 2).
- [ ] Faut-il une option d'images dans ClipVault en v1.1, avec quelles protections (après la v1.0) ?
- [ ] Windows 10 : simple tolérance ou support testé (lot 8) ?
- [ ] Raccourcis par défaut à confirmer après essai sur le poste cible : Ctrl+Alt+O (OCR), Ctrl+Alt+H (ClipVault), Ctrl+K (palette, dans la fenêtre uniquement) (lot 4).
