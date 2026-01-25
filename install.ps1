Write-Host "Installing ttyt..."

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed. Please install Python 3.8+ first."
    exit 1
}

$configDir = "$HOME\.ttyt"
if (-not (Test-Path $configDir)) {
    Write-Host "Creating configuration directory at $configDir..."
    New-Item -ItemType Directory -Force -Path $configDir | Out-Null
}

Write-Host "Installing package and dependencies..."
pip install .

if ($LASTEXITCODE -eq 0) {
    Write-Host "--------------------------------------------------"
    Write-Host "Installation successful!"
    Write-Host "You can now run 'ttyt' from your terminal."
    Write-Host "Configuration is stored in $configDir"
    Write-Host "--------------------------------------------------"
} else {
    Write-Error "Installation failed. Please check the error messages above."
    exit 1
}
