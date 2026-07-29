<#
.SYNOPSIS
    Starts the Hermes Email Marketing Agent with all components.
.DESCRIPTION
    This script starts the database migrations, seeds demo data, launches the web server,
    and starts the Celery worker and beat scheduler.
.NOTES
    File Name      : start.ps1
    Prerequisite   : PowerShell 5.1+
    Author         : Hermes Setup Script
#>

# Set execution policy for this session
Set-ExecutionPolicy Bypass -Scope Process -Force

# Function to display colored messages
function Write-ColorMessage {
    param (
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Function to check if a process is running
function Test-ProcessRunning {
    param (
        [string]$ProcessName
    )
    return (Get-Process -Name $ProcessName -ErrorAction SilentlyContinue) -ne $null
}

# Function to run database migrations
function Run-DatabaseMigrations {
    Write-ColorMessage "🚀 Running database migrations..." "Cyan"
    try {
        & "C:\Users\Rupesh\AppData\Local\Programs\Python\Python312\python.exe" -m alembic upgrade head
        Write-ColorMessage "✅ Database migrations completed successfully!" "Green"
    } catch {
        Write-ColorMessage "❌ Database migrations failed: $_" "Red"
        exit 1
    }
}

# Function to seed demo data
function Run-SeedData {
    Write-ColorMessage "🌱 Seeding demo data..." "Cyan"
    try {
        & "C:\Users\Rupesh\AppData\Local\Programs\Python\Python312\python.exe" scripts/seed_demo.py
        Write-ColorMessage "✅ Demo data seeded successfully!" "Green"
    } catch {
        Write-ColorMessage "❌ Seeding failed: $_" "Red"
        exit 1
    }
}

# Function to start the web server
function Start-WebServer {
    Write-ColorMessage "🌐 Starting web server..." "Cyan"
    try {
        Start-Process -NoNewWindow -FilePath "C:\Users\Rupesh\AppData\Local\Programs\Python\Python312\python.exe" -ArgumentList "-m uvicorn app.main:app --reload"
        Write-ColorMessage "✅ Web server started on http://localhost:8000" "Green"
    } catch {
        Write-ColorMessage "❌ Web server failed to start: $_" "Red"
        exit 1
    }
}

# Function to start Celery worker
function Start-CeleryWorker {
    Write-ColorMessage "👷 Starting Celery worker..." "Cyan"
    try {
        Start-Process -NoNewWindow -FilePath "C:\Users\Rupesh\AppData\Local\Programs\Python\Python312\python.exe" -ArgumentList "-m celery -A app.workers.celery_app worker -l info"
        Write-ColorMessage "✅ Celery worker started" "Green"
    } catch {
        Write-ColorMessage "❌ Celery worker failed to start: $_" "Red"
        exit 1
    }
}

# Function to start Celery beat
function Start-CeleryBeat {
    Write-ColorMessage "⏰ Starting Celery beat scheduler..." "Cyan"
    try {
        Start-Process -NoNewWindow -FilePath "C:\Users\Rupesh\AppData\Local\Programs\Python\Python312\python.exe" -ArgumentList "-m celery -A app.workers.celery_app beat -l info"
        Write-ColorMessage "✅ Celery beat scheduler started" "Green"
    } catch {
        Write-ColorMessage "❌ Celery beat failed to start: $_" "Red"
        exit 1
    }
}

# Function to check Python installation
function Check-PythonInstallation {
    Write-ColorMessage "🐍 Checking Python installation..." "Cyan"
    $pythonPath = "C:\Users\Rupesh\AppData\Local\Programs\Python\Python312\python.exe"
    if (-not (Test-Path $pythonPath)) {
        Write-ColorMessage "❌ Python 3.12 not found at expected path: $pythonPath" "Red"
        Write-ColorMessage "Please install Python 3.12 or update the path in start.ps1" "Yellow"
        exit 1
    }
    Write-ColorMessage "✅ Python 3.12 found" "Green"
}

# Function to install required packages
function Install-Packages {
    Write-ColorMessage "📦 Installing required packages..." "Cyan"
    try {
        & "C:\Users\Rupesh\AppData\Local\Programs\Python\Python312\python.exe" -m pip install -e .
        Write-ColorMessage "✅ Packages installed successfully!" "Green"
    } catch {
        Write-ColorMessage "❌ Package installation failed: $_" "Red"
        exit 1
    }
}

# Main execution
function Main {
    # Display header
    Write-ColorMessage "=========================================" "Magenta"
    Write-ColorMessage "  Hermes Email Marketing Agent" "Magenta"
    Write-ColorMessage "  Comprehensive Startup Script" "Magenta"
    Write-ColorMessage "=========================================" "Magenta"
    Write-ColorMessage ""

    # Check Python
    Check-PythonInstallation

    # Install packages
    Install-Packages

    # Run migrations
    Run-DatabaseMigrations

    # Seed data
    Run-SeedData

    # Start components
    Start-WebServer
    Start-CeleryWorker
    Start-CeleryBeat

    # Display completion message
    Write-ColorMessage ""
    Write-ColorMessage "=========================================" "Magenta"
    Write-ColorMessage "  🎉 All components started!" "Magenta"
    Write-ColorMessage "=========================================" "Magenta"
    Write-ColorMessage ""
    Write-ColorMessage "🌐 Web Dashboard: http://localhost:8000" "White"
    Write-ColorMessage "📖 API Docs:      http://localhost:8000/docs" "White"
    Write-ColorMessage ""
    Write-ColorMessage "Press Ctrl+C in each terminal to stop services" "Yellow"
    Write-ColorMessage "=========================================" "Magenta"
}

# Run the main function
Main