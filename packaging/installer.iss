; Inno Setup 6: crea l'installer Windows dalla cartella generata da PyInstaller.
; Compilare con: iscc packaging\installer.iss
#define AppName "Veridica"
#define AppVersion "1.5.1"
[Setup]
AppId={{6F1C2A54-8C1E-4D7B-9A3F-2B7E5D1C0A91}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={autopf}\Veridica
DefaultGroupName={#AppName}
OutputDir=..\dist\installer
OutputBaseFilename=Veridica-{#AppVersion}-setup
Compression=lzma2/max
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequiredOverridesAllowed=dialog
WizardStyle=modern
SetupIconFile=..\src\fvp\ui\assets\fvp.ico
UninstallDisplayIcon={app}\Veridica.exe
[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
[Files]
Source: "..\dist\Veridica\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
Source: "..\docs\*"; DestDir: "{app}\docs"; Flags: recursesubdirs ignoreversion
[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\Veridica.exe"
Name: "{group}\Manuale utente"; Filename: "{app}\docs\MANUALE_UTENTE.md"
Name: "{group}\Crediti e licenze di terze parti"; Filename: "{app}\THIRD_PARTY_NOTICES.md"
Name: "{group}\Testi delle licenze"; Filename: "{app}\licenses"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\Veridica.exe"; Tasks: desktopicon
[Tasks]
Name: "desktopicon"; Description: "Crea un'icona sul desktop"; Flags: unchecked
