"""Page Paramètres : onglets Général et Apparence (section 15).

Chaque changement est appliqué immédiatement (pas de bouton Enregistrer), conformément à
« appliqués sans redémarrage sauf mention contraire ». Un bouton « Rétablir les valeurs par
défaut » est présent sur la page comme l'exige la section 15 (un par onglet serait
prématuré tant qu'il n'y a que deux onglets au lot 0).
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from nexusdesk.config.schema import AppearanceSettings, AppSettings, GeneralSettings
from nexusdesk.viewmodels.settings_viewmodel import SettingsViewModel

_HOME_PAGE_LABELS = {
    "dashboard": "Tableau de bord",
    "app_manager": "AppManager",
    "netwatch": "NetWatch",
    "screentext": "ScreenText",
    "logdoctor": "LogDoctor",
    "diskpilot": "DiskPilot",
    "clipvault": "ClipVault",
}

_CLOSE_BEHAVIOR_LABELS = {"minimize": "Réduire dans la zone de notification", "quit": "Quitter"}
_THEME_LABELS = {"dark": "Sombre", "light": "Clair", "system": "Suivre Windows"}
_DENSITY_LABELS = {"comfortable": "Confortable", "compact": "Compacte"}
_TEXT_SIZE_LABELS = {"small": "Petite", "medium": "Moyenne", "large": "Grande"}


def _populate_combo(combo: QComboBox, labels: dict[str, str], current: str) -> None:
    for value, label in labels.items():
        combo.addItem(label, value)
    index = combo.findData(current)
    if index >= 0:
        combo.setCurrentIndex(index)


class SettingsPage(QWidget):
    def __init__(self, viewmodel: SettingsViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._loading = False

        title = QLabel("Paramètres")
        title.setProperty("role", "pageTitle")

        tabs = QTabWidget()
        tabs.addTab(self._build_general_tab(), "Général")
        tabs.addTab(self._build_appearance_tab(), "Apparence")

        reset_button = QPushButton("Rétablir les valeurs par défaut")
        reset_button.clicked.connect(self._on_reset_clicked)

        footer = QHBoxLayout()
        footer.addStretch(1)
        footer.addWidget(reset_button)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(tabs, stretch=1)
        layout.addLayout(footer)

        self._load_from_settings(viewmodel.settings)
        viewmodel.settings_changed.connect(self._load_from_settings)

    def _build_general_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)

        self._startup_checkbox = QCheckBox("Lancer NexusDesk au démarrage de Windows")
        self._startup_checkbox.toggled.connect(self._on_field_changed)
        form.addRow(self._startup_checkbox)

        self._close_behavior_combo = QComboBox()
        self._close_behavior_combo.currentIndexChanged.connect(self._on_field_changed)
        form.addRow("Fermer la fenêtre :", self._close_behavior_combo)

        self._home_page_combo = QComboBox()
        self._home_page_combo.currentIndexChanged.connect(self._on_field_changed)
        form.addRow("Page d'accueil :", self._home_page_combo)

        self._developer_mode_checkbox = QCheckBox("Mode développeur")
        self._developer_mode_checkbox.toggled.connect(self._on_field_changed)
        form.addRow(self._developer_mode_checkbox)

        return tab

    def _build_appearance_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)

        self._theme_combo = QComboBox()
        self._theme_combo.currentIndexChanged.connect(self._on_field_changed)
        form.addRow("Thème :", self._theme_combo)

        self._mica_checkbox = QCheckBox("Effet Mica")
        self._mica_checkbox.toggled.connect(self._on_field_changed)
        form.addRow(self._mica_checkbox)

        self._density_combo = QComboBox()
        self._density_combo.currentIndexChanged.connect(self._on_field_changed)
        form.addRow("Densité :", self._density_combo)

        self._text_size_combo = QComboBox()
        self._text_size_combo.currentIndexChanged.connect(self._on_field_changed)
        form.addRow("Taille du texte :", self._text_size_combo)

        self._animations_checkbox = QCheckBox("Animations")
        self._animations_checkbox.toggled.connect(self._on_field_changed)
        form.addRow(self._animations_checkbox)

        return tab

    def _load_from_settings(self, settings: AppSettings) -> None:
        self._loading = True
        try:
            self._startup_checkbox.setChecked(settings.general.launch_at_startup)
            self._close_behavior_combo.clear()
            _populate_combo(
                self._close_behavior_combo, _CLOSE_BEHAVIOR_LABELS, settings.general.close_behavior
            )
            self._home_page_combo.clear()
            _populate_combo(self._home_page_combo, _HOME_PAGE_LABELS, settings.general.home_page)
            self._developer_mode_checkbox.setChecked(settings.general.developer_mode)

            self._theme_combo.clear()
            _populate_combo(self._theme_combo, _THEME_LABELS, settings.appearance.theme)
            self._mica_checkbox.setChecked(settings.appearance.mica_enabled)
            self._density_combo.clear()
            _populate_combo(self._density_combo, _DENSITY_LABELS, settings.appearance.density)
            self._text_size_combo.clear()
            _populate_combo(self._text_size_combo, _TEXT_SIZE_LABELS, settings.appearance.text_size)
            self._animations_checkbox.setChecked(settings.appearance.animations_enabled)
        finally:
            self._loading = False

    def _on_field_changed(self) -> None:
        if self._loading:
            return
        general = GeneralSettings(
            launch_at_startup=self._startup_checkbox.isChecked(),
            close_behavior=self._close_behavior_combo.currentData(),
            home_page=self._home_page_combo.currentData(),
            developer_mode=self._developer_mode_checkbox.isChecked(),
        )
        appearance = AppearanceSettings(
            theme=self._theme_combo.currentData(),
            mica_enabled=self._mica_checkbox.isChecked(),
            density=self._density_combo.currentData(),
            text_size=self._text_size_combo.currentData(),
            animations_enabled=self._animations_checkbox.isChecked(),
        )
        self._viewmodel.save(AppSettings(general=general, appearance=appearance))

    def _on_reset_clicked(self) -> None:
        self._viewmodel.reset_to_defaults()
