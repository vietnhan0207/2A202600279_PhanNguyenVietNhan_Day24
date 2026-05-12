# Lệnh cài đặt git-secrets cho Windows PowerShell

Write-Host "Cloning git-secrets repository..."
git clone https://github.com/awslabs/git-secrets.git $env:TEMP\git-secrets

Write-Host "Installing git-secrets..."
Set-Location $env:TEMP\git-secrets
.\install.ps1

Write-Host "Initializing project repository..."
Set-Location "C:\GET_A_JOB\VIN_AI\Lab\Day24\2A202600279_PhanNguyenVietNhan_Day24\medviet-governance"
git init
git secrets --install
git secrets --register-aws

Write-Host "Adding custom pattern for 12-digit CCCD..."
git secrets --add '\b\d{12}\b'

Write-Host "Setup complete! You can test it by trying to commit a file containing a 12-digit number."
