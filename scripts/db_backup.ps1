# VERIMETER Database Backup Automation Script
# Usage: powershell -File scripts/db_backup.ps1

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $PSScriptRoot "../backups"

if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

Write-Output "=== Starting VERIMETER Database Backup Process ==="

# Check environment variable for DATABASE_URL
$DbUrl = $env:DATABASE_URL

if (-not $DbUrl) {
    # Default to SQLite local database file
    $DbFile = "verimeter.db"
    $BackupFile = Join-Path $BackupDir "verimeter_backup_$Timestamp.db"
    
    if (Test-Path $DbFile) {
        Copy-Item -Path $DbFile -Destination $BackupFile
        Write-Output "Successfully backed up SQLite database to: $BackupFile"
    } else {
        Write-Output "SQLite database file ($DbFile) does not exist yet. Run application first."
    }
} elseif ($DbUrl -like "*postgresql*") {
    $BackupFile = Join-Path $BackupDir "verimeter_postgres_backup_$Timestamp.sql"
    Write-Output "PostgreSQL configuration detected."
    Write-Output "Executing pg_dump..."
    
    try {
        # Extract connection details from Postgres URI (e.g. postgresql://user:pass@host:port/dbname)
        # We run pg_dump using the URL directly
        pg_dump --dbname=$DbUrl --file=$BackupFile --clean --create
        if ($LASTEXITCODE -eq 0) {
             Write-Output "Successfully backed up PostgreSQL database to: $BackupFile"
        } else {
             Write-Output "Error: pg_dump command failed with exit code $LASTEXITCODE. Ensure PostgreSQL client tools are in the PATH."
        }
    } catch {
        Write-Output "Error calling pg_dump: $_"
    }
} else {
    Write-Output "Unsupported database connection scheme for automated backup. Skipped."
}

Write-Output "=== Backup Process Finished ==="
