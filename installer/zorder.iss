; Zorder Bill Editor Installer Script
; Inno Setup 6.0+ required

[Setup]
AppName=Zorder Bill Editor
AppVersion=1.0.0
AppPublisher=Zorder Technologies
AppPublisherURL=https://github.com/yourusername/zorder
DefaultDirName={pf64}\Zorder
DefaultGroupName=Zorder Bill Editor
OutputBaseFilename=ZorderInstaller
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startmenu"; Description: "Create Start Menu shortcuts"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checked

[Files]
Source: "dist\agent.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\console.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "agent\.env.example"; DestDir: "{app}"; DestName: "agent.env.example"; Flags: ignoreversion
Source: "console\.env.example"; DestDir: "{app}"; DestName: "console.env.example"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "install_task.ps1"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Zorder Console"; Filename: "{app}\console.exe"
Name: "{group}\{cm:UninstallProgram,Zorder Bill Editor}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Zorder Console"; Filename: "{app}\console.exe"; Tasks: desktopicon

[Run]
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\install_task.ps1"""; Flags: runhidden; Description: "Install Scheduled Task"

[UninstallRun]
Filename: "schtasks.exe"; Parameters: "/delete /tn ""ZorderAgent"" /f"; Flags: runhidden

[Code]
function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstPath := ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\{#emit SetupSetting("AppId")}_is1');
  sUnInstallString := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

function IsUpgrade(): Boolean;
begin
  Result := (GetUninstallString() <> '');
end;

function InitializeSetup(): Boolean;
var
  V: Integer;
  iResultCode: Integer;
  sUnInstallString: String;
begin
  Result := True;
  
  // Check if app is already installed
  if RegValueExists(HKEY_LOCAL_MACHINE,'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#emit SetupSetting("AppId")}_is1', 'UninstallString') then
  begin
    V := MsgBox(ExpandConstant('Zorder Bill Editor is already installed. Do you want to uninstall the previous version?'), mbInformation, MB_YESNO);
    if V = IDYES then
    begin
      sUnInstallString := GetUninstallString();
      sUnInstallString := RemoveQuotes(sUnInstallString);
      if Exec(sUnInstallString, '/SILENT', '', SW_HIDE, ewWaitUntilTerminated, iResultCode) then
        Result := True
      else
        Result := False;
    end
    else
      Result := False;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Create application data directory
    ForceDirectories(ExpandConstant('{userappdata}\Zorder'));
  end;
end;


