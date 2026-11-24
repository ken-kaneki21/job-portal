param(
    [Parameter(Mandatory=$true)][string]$Python,
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [switch]$PreflightOnly
)
$ErrorActionPreference = 'Stop'
$Python = (Resolve-Path -LiteralPath $Python).Path
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $OutputDirectory -ErrorAction Stop | Out-Null
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $root
$project = 'jobintel-gate-' + [guid]::NewGuid().ToString('N').Substring(0,12)
$config = @('compose','-p',$project,'-f','docker-compose.yml','-f','scripts/compose.acceptance.yml')
$services = @('postgres','temporal-postgres','temporal')
$api = $null
$started = $false
$stage = 'configuration'
$evidence = [ordered]@{ project=$project; status='blocked'; stage=$stage }
$exitCode = 2

function Free-Port {
    $listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,0)
    try { $listener.Start(); return $listener.LocalEndpoint.Port }
    finally { $listener.Stop() }
}

try {
    $evidence.commit = (git rev-parse HEAD)
    $env:JOBINTEL_POSTGRES_DB = 'fixture'
    $env:JOBINTEL_POSTGRES_USER = 'fixture'
    $env:JOBINTEL_POSTGRES_PASSWORD = [guid]::NewGuid().ToString('N')
    $env:TEMPORAL_POSTGRES_DB = 'temporal'
    $env:TEMPORAL_POSTGRES_USER = 'fixture'
    $env:TEMPORAL_POSTGRES_PASSWORD = [guid]::NewGuid().ToString('N')
    $env:JOBINTEL_DOCKER_DATABASE_URL = "postgresql+psycopg://fixture:${env:JOBINTEL_POSTGRES_PASSWORD}@postgres:5432/fixture"
    $env:ACCEPTANCE_PG_PORT = '55472'
    $env:ACCEPTANCE_TEMPORAL_PORT = '57272'
    $ports = @()
    if (-not $PreflightOnly) {
        $stage = 'docker_engine'
        $engine = docker version --format '{{.Server.Version}}' 2>&1
        if ($LASTEXITCODE -ne 0) { throw ($engine -join [Environment]::NewLine) }
        $evidence.docker_version = "$engine"
        $stage = 'allocate_loopback_ports'
        while ($ports.Count -lt 3) {
            $port = Free-Port
            if ($port -notin $ports) { $ports += $port }
        }
        $env:ACCEPTANCE_PG_PORT = "$($ports[0])"
        $env:ACCEPTANCE_TEMPORAL_PORT = "$($ports[1])"
    }
    $stage = 'compose_configuration'
    $model = docker @config config --format json | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0) { throw 'Compose config failed' }
    foreach ($service in $services) {
        $entry = $model.services.$service
        $published = @($entry.ports | Where-Object { $_ -and $_.host_ip -ne '127.0.0.1' })
        if (-not $entry -or $entry.container_name -or $published.Count) {
            throw "Isolation check failed for $service"
        }
    }
    foreach ($name in @('jobintel_postgres','jobintel_temporal_postgres')) {
        if ($model.volumes.$name.external -or $model.volumes.$name.name -ne "${project}_$name") {
            throw "Volume is outside the disposable project: $name"
        }
    }
    $evidence.images = @($services | ForEach-Object { $model.services.$_.image })
    if ($PreflightOnly) {
        $evidence.status = 'configuration_validated'
        $exitCode = 0
    } else {
        $stage = 'cached_images'
        foreach ($image in $evidence.images) {
            docker image inspect --format '{{.Id}}' $image | Out-Null
            if ($LASTEXITCODE -ne 0) { throw "Required cached image unavailable: $image" }
        }
        $stage = 'compose_start'
        $started = $true
        docker @config up -d --pull never --no-build --wait --wait-timeout 60 @services
        if ($LASTEXITCODE -ne 0) { throw 'Isolated stack failed to start' }
        $env:DATABASE_URL = "postgresql+psycopg://fixture:${env:JOBINTEL_POSTGRES_PASSWORD}@127.0.0.1:$($ports[0])/fixture"
        $env:JOBINTEL_TEMPORAL_ADDRESS = "127.0.0.1:$($ports[1])"
        $env:PYTHONPATH = (Join-Path $root 'src')
        $env:HF_HUB_OFFLINE = '1'
        $env:TRANSFORMERS_OFFLINE = '1'
        $env:JOBINTEL_EMBEDDING_BACKEND = 'torch'
        $env:JOBINTEL_PROFILE_NAME = 'screening'
        $env:JOBINTEL_PROFILE_PATH = Join-Path $OutputDirectory 'synthetic-profile.json'
        $env:JOBINTEL_AUTH_USERNAME = 'screening'
        $env:JOBINTEL_AUTH_PASSWORD = [guid]::NewGuid().ToString('N')
        $env:JOBINTEL_SESSION_SECRET = [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')
        $env:JOBINTEL_COOKIE_SECURE = 'false'
        & $Python -c 'import json, os, sys; sys.path.insert(0,"scripts"); from verify_cached_stack import PROFILE; open(os.environ["JOBINTEL_PROFILE_PATH"],"x",encoding="utf8").write(json.dumps(PROFILE))'
        if ($LASTEXITCODE -ne 0) { throw 'Fixture profile could not be written' }
        $stage = 'migrations'
        & $Python -m alembic upgrade head
        if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL migration failed' }
        $stage = 'api_start'
        $api = Start-Process -FilePath $Python -ArgumentList @('-m','uvicorn','jobintel.api:app','--host','127.0.0.1','--port',"$($ports[2])") -WorkingDirectory $root -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $OutputDirectory 'api.log') -RedirectStandardError (Join-Path $OutputDirectory 'api-error.log')
        $apiUrl = "http://127.0.0.1:$($ports[2])"
        $stage = 'temporal_replay_and_authenticated_api'
        & $Python scripts/verify_cached_stack.py $OutputDirectory $apiUrl
        if ($LASTEXITCODE -ne 0) { throw 'Temporal replay or API acceptance failed' }
        $evidence.status = 'accepted'
        $exitCode = 0
    }
} catch {
    $evidence.error = $_.Exception.Message
    if ($started) { $evidence.status = 'failed'; $exitCode = 1 }
    Write-Error -ErrorAction Continue $evidence.error
} finally {
    if ($api -and -not $api.HasExited) { Stop-Process -Id $api.Id -ErrorAction SilentlyContinue }
    if ($started) { docker @config stop --timeout 10 @services }
    $evidence.stage = $stage
    $evidence | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'gate.json') -Encoding utf8
    Pop-Location
}
exit $exitCode
