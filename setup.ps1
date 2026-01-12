# One-time setup script for Windows
Write-Host "Setting up Startup Automation..." -ForegroundColor Cyan

# 1. Create virtual environment
Write-Host "`n[1/4] Creating Python virtual environment..."
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install dependencies
Write-Host "`n[2/4] Installing Python packages..."
pip install -r requirements.txt

# 3. Install Playwright browsers
Write-Host "`n[3/4] Installing Playwright browsers..."
playwright install chromium

# 4. Create directories
Write-Host "`n[4/4] Creating directories..."
New-Item -ItemType Directory -Force -Path "logs"
New-Item -ItemType Directory -Force -Path "browser_data/work_profile"
New-Item -ItemType Directory -Force -Path "browser_data/personal_profile"

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "`nTo test, run: python main.py --dry-run"
