# NexusDesk

Boîte à outils Windows locale, gratuite et sans télémétrie : aucun compte, aucun abonnement,
aucune donnée envoyée. Le projet est livré par lots ; cette préversion contient le **socle** et
le module **DiskPilot** (analyse de l'espace disque).

> **Préversion 0.2.1-beta.3.** Les modules AppManager, NetWatch, ScreenText, LogDoctor,
> ClipVault et le tableau de bord ne sont pas encore développés : leur page l'indique
> clairement et ne propose aucune fonction.

## Installation

Configuration requise : Windows 10 ou 11, 64 bits. **Python n'est pas nécessaire.**

Téléchargez les fichiers depuis la page
[Releases](https://github.com/RRRR-boop/NexusDesk---App/releases) :

- **Installateur** `NexusDesk-v<version>-Setup.exe` : installation pour l'utilisateur
  courant, sans droits administrateur, dans `%LOCALAPPDATA%\Programs\NexusDesk`, avec un
  raccourci dans le menu Démarrer. La désinstallation (Paramètres Windows → Applications)
  conserve vos données.
- **Archive portable** `NexusDesk-v<version>-portable.zip` : décompressez-la où vous
  voulez puis lancez `NexusDesk.exe`. Grâce au fichier `portable.flag`, toutes les données
  restent dans le dossier de l'application.

Vérifiez l'intégrité des fichiers avec `SHA256SUMS.txt` :

```powershell
Get-FileHash .\NexusDesk-v<version>-Setup.exe -Algorithm SHA256
```

L'exécutable n'est pas signé : Windows SmartScreen peut afficher « Windows a protégé votre
ordinateur ». Choisissez « Informations complémentaires » puis « Exécuter quand même » si la
somme SHA-256 correspond.

Données (version installée) : `%LOCALAPPDATA%\NexusDesk` (bases SQLite, journaux, sauvegardes).

## Fonctionnalités de cette version

### Socle

- Une seule instance : relancer NexusDesk rouvre la fenêtre existante.
- Icône dans la zone de notification ; la croix réduit la fenêtre ou quitte (réglable).
- Navigation `Ctrl+1` à `Ctrl+7`, thèmes sombre, clair ou « suivre Windows ».
- Paramètres enregistrés et appliqués immédiatement (Général, Apparence, DiskPilot).
- Opérations longues en arrière-plan, annulables, sans figer l'interface.
- Journaux techniques locaux, sans le nom du profil utilisateur ; page Diagnostic.
- Bases de données migrées automatiquement, avec sauvegarde et restauration en cas d'échec.

### DiskPilot

- Volumes : lettre, nom, système de fichiers, type, jauge d'espace libre (seuils réglables).
- Analyse d'un dossier : tailles logique et sur disque, liens physiques comptés une seule
  fois, jonctions et liens symboliques jamais suivis, fichiers OneDrive à la demande jamais
  téléchargés. Annulable à tout moment.
- Carte proportionnelle (treemap) navigable par double-clic, colorée par catégorie.
- Plus gros fichiers, doublons (taille puis empreinte, avec cache), suggestions de nettoyage
  présentées comme des pistes à vérifier.
- Suppression **uniquement vers la Corbeille**, après aperçu et confirmation explicite ;
  revérification de chaque fichier juste avant, refus des fichiers système, protégés ou
  verrouillés.
- Historique des 5 dernières analyses par dossier et comparaison entre deux analyses.
- Export CSV (fichiers, dossiers, doublons).
- Exclusions par défaut (`Windows`, `Program Files`, `ProgramData`, Corbeille…) et dossiers
  exclus personnalisés. Un dossier exclu peut être analysé explicitement, en lecture seule.

## Limitations connues

- Les grosses analyses sont plus lentes que l'objectif du cahier des charges : environ 3 à
  5 minutes pour 1 million de fichiers au lieu de 3, surtout à cause de l'antivirus en temps
  réel. La mémoire utilisée atteint environ 1,1 Go pour 1 million de fichiers.
- Pas de suppression définitive.
- Non vérifiés : Narrateur Windows, écrans à mises à l'échelle différentes, rendu de l'effet
  Mica.

Détails : [CHANGELOG.md](CHANGELOG.md) et `docs/journal-des-lots.md`.

## Développement

```powershell
./scripts/install-dev.ps1       # environnement (uv, Python 3.12, hooks pre-commit)
./scripts/run.ps1 -Dev          # lance l'application depuis les sources
./scripts/check.ps1             # Ruff, mypy --strict, import-linter, pip-audit
./scripts/test.ps1 -Integration -Coverage
./scripts/build.ps1             # empaquetage PyInstaller (dist\NexusDesk)
./scripts/smoke-test.ps1        # démarrage, réouverture et arrêt de l'exécutable
./scripts/package-release.ps1   # ZIP portable, installateur, VERSION.txt, SHA256SUMS.txt
```

Sous Windows PowerShell 5.1, lancez les scripts avec
`powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\<script>.ps1`.

Le cahier des charges complet est dans `docs/cahier-des-charges-v2.md` ; l'architecture dans
`docs/architecture.md` et les décisions dans `docs/adr/`.

## Licence

NexusDesk est un logiciel libre distribué sous licence **GNU General Public License v3.0**
(`GPL-3.0-only`) : voir le fichier [LICENSE](LICENSE). Vous pouvez l'utiliser, l'étudier, le
modifier et le redistribuer selon les termes de cette licence ; toute version redistribuée,
modifiée ou non, doit rester sous GPL v3 avec son code source.

Chaque distribution contient `LICENSE` (texte intégral de la GPL v3) et
`THIRD-PARTY-LICENSES.txt` (avis et textes de licence des composants embarqués). Toutes ces
licences sont compatibles avec la GPL v3 ; Qt/PySide6 est utilisé sous LGPL v3, ses
bibliothèques restant des fichiers séparés et remplaçables. Le code source correspondant à
chaque version publiée est disponible sur ce dépôt, au tag `v<version>`. L'inventaire des
licences de toutes les dépendances (développement compris) est dans `docs/licences-tierces.md`.
