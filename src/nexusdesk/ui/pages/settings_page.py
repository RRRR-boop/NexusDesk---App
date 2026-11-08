"""Page Paramètres : onglets Général, Apparence et DiskPilot (section 15).

Chaque changement est appliqué immédiatement (pas de bouton Enregistrer), conformément à
« appliqués sans redémarrage sauf mention contraire ». Un bouton « Rétablir les valeurs par
défaut » est présent sur la page comme l'exige la section 15.

L'onglet DiskPilot n'expose que les réglages réellement câblés (taille minimale des
doublons, seuils d'alerte d'espace libre, dossiers exclus) : la suppression définitive n'est pas
implémentée, elle n'a donc aucun contrôle (principe « aucun bouton factice »).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from nexusdesk.config.schema import (
    AppearanceSettings,
    AppSettings,
    DiskPilotSettings,
    GeneralSettings,
)
from nexusdesk.viewmodels.settings_viewmodel import SettingsViewModel

_BYTES_PER_MB = 1024 * 1024

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
        tabs.addTab(self._build_diskpilot_tab(), "DiskPilot")

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

    def _build_diskpilot_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)

        self._min_duplicate_size_spin = QDoubleSpinBox()
        self._min_duplicate_size_spin.setRange(0.01, 10_240.0)
        self._min_duplicate_size_spin.setDecimals(2)
        self._min_duplicate_size_spin.setSuffix(" Mo")
        self._min_duplicate_size_spin.valueChanged.connect(self._on_field_changed)
        form.addRow("Taille minimale des doublons :", self._min_duplicate_size_spin)

        self._warning_free_spin = QDoubleSpinBox()
        self._warning_free_spin.setRange(1.0, 90.0)
        self._warning_free_spin.setDecimals(0)
        self._warning_free_spin.setSuffix(" %")
        self._warning_free_spin.valueChanged.connect(self._on_field_changed)
        form.addRow("Avertissement sous (espace libre) :", self._warning_free_spin)

        self._alert_free_spin = QDoubleSpinBox()
        self._alert_free_spin.setRange(0.0, 89.0)
        self._alert_free_spin.setDecimals(0)
        self._alert_free_spin.setSuffix(" %")
        self._alert_free_spin.valueChanged.connect(self._on_field_changed)
        form.addRow("Alerte sous (espace libre) :", self._alert_free_spin)

        self._exclusions_list = QListWidget()
        self._exclusions_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._exclusions_list.setMaximumHeight(140)
        self._exclusions_list.itemSelectionChanged.connect(self._on_exclusion_selection_changed)
        add_exclusion_button = QPushButton("Ajouter un dossier…")
        add_exclusion_button.clicked.connect(self._on_add_exclusion_clicked)
        self._remove_exclusion_button = QPushButton("Retirer")
        self._remove_exclusion_button.setEnabled(False)
        self._remove_exclusion_button.clicked.connect(self._on_remove_exclusion_clicked)
        exclusion_buttons = QHBoxLayout()
        exclusion_buttons.addWidget(add_exclusion_button)
        exclusion_buttons.addWidget(self._remove_exclusion_button)
        exclusion_buttons.addStretch(1)
        exclusions_box = QVBoxLayout()
        exclusions_box.addWidget(self._exclusions_list)
        exclusions_box.addLayout(exclusion_buttons)
        form.addRow("Dossiers exclus des analyses :", exclusions_box)

        note = QLabel(
            "Les exclusions système (Windows, Program Files, Corbeille…) s'appliquent toujours. "
            "Les fichiers supprimés depuis DiskPilot sont toujours envoyés à la Corbeille : "
            "la suppression définitive n'est pas disponible."
        )
        note.setWordWrap(True)
        form.addRow(note)

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

            diskpilot = settings.diskpilot
            self._min_duplicate_size_spin.setValue(
                diskpilot.min_duplicate_size_bytes / _BYTES_PER_MB
            )
            self._warning_free_spin.setValue(diskpilot.warning_free_percent)
            self._alert_free_spin.setValue(diskpilot.alert_free_percent)
            self._exclusions_list.clear()
            self._exclusions_list.addItems(diskpilot.extra_excluded_paths)
        finally:
            self._loading = False

    def _on_field_changed(self) -> None:
        if self._loading:
            return
        # Le seuil d'alerte doit rester strictement sous le seuil d'avertissement, sinon
        # l'état « avertissement » de la jauge DiskPilot deviendrait inatteignable.
        if self._alert_free_spin.value() >= self._warning_free_spin.value():
            self._loading = True
            try:
                self._alert_free_spin.setValue(self._warning_free_spin.value() - 1)
            finally:
                self._loading = False
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
        # Partir des réglages DiskPilot courants : les champs sans contrôle d'interface
        # (exclusions, suppression définitive) ne doivent jamais être remis à leur valeur
        # par défaut par un changement fait dans un autre onglet.
        diskpilot: DiskPilotSettings = self._viewmodel.settings.diskpilot.model_copy(
            update={
                "min_duplicate_size_bytes": round(
                    self._min_duplicate_size_spin.value() * _BYTES_PER_MB
                ),
                "warning_free_percent": self._warning_free_spin.value(),
                "alert_free_percent": self._alert_free_spin.value(),
                "extra_excluded_paths": self._current_exclusions(),
            }
        )
        self._viewmodel.save(
            self._viewmodel.settings.model_copy(
                update={"general": general, "appearance": appearance, "diskpilot": diskpilot}
            )
        )

    def _current_exclusions(self) -> list[str]:
        return [
            self._exclusions_list.item(row).text() for row in range(self._exclusions_list.count())
        ]

    def add_exclusion(self, directory: str) -> None:
        """Ajoute un dossier absolu (normalisé, sans doublon insensible à la casse)."""
        path = Path(directory)
        if not path.is_absolute():
            return
        normalized = str(path)
        if any(Path(existing) == path for existing in self._current_exclusions()):
            return
        self._exclusions_list.addItem(normalized)
        self._on_field_changed()

    def _on_add_exclusion_clicked(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Choisir un dossier à exclure")
        if directory:
            self.add_exclusion(directory)

    def _on_remove_exclusion_clicked(self) -> None:
        for item in self._exclusions_list.selectedItems():
            self._exclusions_list.takeItem(self._exclusions_list.row(item))
        self._on_field_changed()

    def _on_exclusion_selection_changed(self) -> None:
        self._remove_exclusion_button.setEnabled(bool(self._exclusions_list.selectedItems()))

    def _on_reset_clicked(self) -> None:
        self._viewmodel.reset_to_defaults()
