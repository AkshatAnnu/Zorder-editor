# PowerShell script to install Scheduled Task for Zorder Agent
# This script is run by the Inno Setup installer

param(
    [string]$InstallPath = "${env:ProgramFiles}\Zorder"
)

Write-Host "Installing Zorder Agent Scheduled Task..."

try {
    # Define task parameters
    $TaskName = "ZorderAgent"
    $ExePath = Join-Path $InstallPath "agent.exe"
    $Description = "Zorder Bill Editor Agent - Automated login and screen recording"
    
    # Check if agent.exe exists
    if (-not (Test-Path $ExePath)) {
        Write-Error "Agent executable not found: $ExePath"
        exit 1
    }
    
    # Delete existing task if it exists
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "Removing existing scheduled task..."
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    # Create new scheduled task
    Write-Host "Creating scheduled task: $TaskName"
    
    # Create task action
    $Action = New-ScheduledTaskAction -Execute $ExePath -WorkingDirectory $InstallPath
    
    # Create task trigger (at logon)
    $Trigger = New-ScheduledTaskTrigger -AtLogOn
    
    # Create task principal (run as current user with highest privileges)
    $Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
    
    # Create task settings
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -DontStopOnIdleEnd
    
    # Register the scheduled task
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Description $Description
    
    Write-Host "Scheduled task created successfully!"
    Write-Host "The Zorder Agent will start automatically when you log in."
    Write-Host ""
    Write-Host "To manually start the agent now, run:"
    Write-Host "Start-ScheduledTask -TaskName '$TaskName'"
    
} catch {
    Write-Error "Failed to create scheduled task: $($_.Exception.Message)"
    exit 1
}

Write-Host "Installation completed successfully!"
