# VERIMETER Deployment Control Script
# Usage: powershell -File scripts/deploy.ps1

Write-Output "=== Starting VERIMETER Containerized Deployment ==="

# Check if docker daemon is running
docker info > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Output "Error: Docker Daemon is not running or docker client is not in PATH."
    Write-Output "Please start Docker Desktop and try again."
    Exit 1
}

Write-Output "Docker Engine detected."
Write-Output "Executing: docker-compose up --build -d"

docker-compose up --build -d

if ($LASTEXITCODE -eq 0) {
    Write-Output ""
    Write-Output "========================================================="
    Write-Output "VERIMETER DEPLOYMENT SUCCESSFUL"
    Write-Output "========================================================="
    Write-Output "The platform services are available at:"
    Write-Output "  - Frontend Dashboard:   http://localhost:3000"
    Write-Output "  - FastAPI REST Backend:  http://localhost:8000"
    Write-Output "  - API Swagger Docs:      http://localhost:8000/docs"
    Write-Output "========================================================="
} else {
    Write-Output "Error: docker-compose command failed with exit code $LASTEXITCODE"
}
