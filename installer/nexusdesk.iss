; Installateur Inno Setup de NexusDesk (section 18 du cahier des charges).
; Compilé par scripts/package-release.ps1, qui fournit AppVersion, SourceDir et OutputDir.
;
; Installation par utilisateur, sans droits administrateur (principe du moindre privilège) :
; dossier %LOCALAPPDATA%\Programs\NexusDesk. Les données de l'application
; (%LOCALAPPDATA%\NexusDesk : bases, journaux, sauvegardes) ne sont jamais supprimées par la
; désinstallation.

#ifndef AppVersion
  #error "AppVersion doit être fourni (/DAppVersion=...)"
#endif
#ifndef SourceDir
  #error "SourceDir doit être fourni (/DSourceDir=...)"
#endif
#ifndef OutputDir
  #define OutputDir "."
#endif

[Setup]
AppId={{6F3C2B1E-8D4A-4E5B-9C7F-2A1D0E9B8C64}
AppName=NexusDesk
AppVersion={#AppVersion}
AppVerName=NexusDesk {#AppVersion}
AppPublisher=NexusDesk
DefaultDirName={localappdata}\Programs\NexusDesk
DefaultGroupName=NexusDesk
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir={#OutputDir}
OutputBaseFilename=NexusDesk-{#AppVersion}-win64-setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\NexusDesk.exe
UninstallDisplayName=NexusDesk {#AppVersion}
CloseApplications=yes
SetupLogging=yes

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\NexusDesk"; Filename: "{app}\NexusDesk.exe"
Name: "{group}\{cm:UninstallProgram,NexusDesk}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\NexusDesk"; Filename: "{app}\NexusDesk.exe"; Tasks: desktopicon

[Registry]
; Retire uniquement l'entrée « Lancer au démarrage » créée par l'application (HKCU, jamais HKLM).
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: none; ValueName: "NexusDesk"; Flags: uninsdeletevalue dontcreatekey

[Run]
Filename: "{app}\NexusDesk.exe"; Description: "{cm:LaunchProgram,NexusDesk}"; Flags: nowait postinstall skipifsilent
