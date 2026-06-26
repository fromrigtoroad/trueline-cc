; Inno Setup script for iRacing Telemetry Overlay

#define AppName "iRacing Telemetry Overlay"
#define AppVersion "1.0.0"
#define AppPublisher "Your Name"
#define AppExeName "iRacingOverlay.exe"

[Setup]
AppId={{B3F2A1C4-8D7E-4F5B-A2C1-9E6D3B0F4A82}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\iRacingOverlay
DefaultGroupName={#AppName}
OutputDir=installer-output
OutputBaseFilename=iRacingOverlay-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
