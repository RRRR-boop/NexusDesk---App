# ADR-0003 — Stockage des paramètres en table clé/valeur

## Statut
Décidé (choix réversible, section 21.3).

## Contexte
Les paramètres (section 15) sont regroupés par onglet, et chaque lot futur ajoutera son
propre onglet (AppManager, NetWatch, ScreenText...). Il faut choisir comment les persister
dans `nexusdesk.db`.

## Options considérées
- **Une colonne par réglage** (table large, un champ par paramètre) : typage SQL précis,
  mais exige une migration Alembic à chaque réglage ajouté par un lot futur.
- **Table clé/valeur** (`key`, `value` JSON, `updated_at`) : un seul schéma stable, validé
  côté application par les modèles pydantic (`config/schema.py`), pas de migration pour un
  nouveau réglage.

## Décision
Table clé/valeur à plat (`models/settings.py`). Les clés suivent une notation pointée
(`general.launch_at_startup`, `appearance.theme`, mais aussi des clés hors schéma déclaré
comme `ui.sidebar_collapsed` pour l'état d'interface). `AppSettings` (pydantic) utilise
`extra="ignore"` au niveau racine pour tolérer ces clés libres sans faire échouer la
reconstruction des onglets Général/Apparence ; chaque sous-modèle (`GeneralSettings`,
`AppearanceSettings`) reste `extra="forbid"` pour détecter une vraie erreur de frappe dans
son propre domaine.

## Conséquences
- `SettingsRepository.get_all()` reconstruit `AppSettings` depuis les clés connues ;
  `get_raw(key, default)` lit une clé libre sans passer par ce schéma.
- Aucune migration Alembic ne sera nécessaire pour les réglages des lots 1 à 8.
