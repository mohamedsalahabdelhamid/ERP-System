@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$f='%~f0'; $o=Join-Path $env:TEMP 'erp_start.ps1'; $l=Get-Content -LiteralPath $f -Encoding UTF8; $i=($l | Select-String '^@@@PS@@@$' | Select-Object -First 1).LineNumber - 1; $l[($i + 1)..($l.Count - 1)] | Set-Content -LiteralPath $o -Encoding UTF8; & $o; Remove-Item -LiteralPath $o -ErrorAction SilentlyContinue"
goto :EOF
@@@PS@@@
$ErrorActionPreference = 'Stop'

function Write-Section($ar, $en) {
    Write-Host ''
    Write-Host ('===== ' + $en + ' =====') -ForegroundColor Cyan
    Write-Host ('===== ' + $ar + ' =====') -ForegroundColor Cyan
}

function Write-Info($ar, $en) {
    Write-Host ('[AR] ' + $ar)
    Write-Host ('[EN] ' + $en)
}

function Invoke-Pause {
    if (-not [Console]::IsOutputRedirected) {
        Read-Host 'اضغط Enter للإغلاق | Press Enter to close'
    }
}

function Test-DockerEngine {
    & docker info *> $null
    return ($LASTEXITCODE -eq 0)
}

function Start-DockerDesktop {
    $paths = @(
        "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
        "$env:LOCALAPPDATA\Docker\Docker Desktop.exe",
        "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe"
    )
    $exe = $paths | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
    if (-not $exe) {
        Write-Info 'Docker Desktop غير مثبّت — شغّل setup.bat أولًا.' 'Docker Desktop not installed - please run setup.bat first.'
        return $false
    }
    Write-Info 'Docker غير مشغّل — جارٍ فتحه تلقائيًا...' 'Docker is not running - starting it now...'
    Start-Process -FilePath $exe
    return $true
}

function Wait-ForDocker {
    if (Test-DockerEngine) {
        Write-Info 'Docker يعمل وجاهز.' 'Docker engine is running and ready.'
        return $true
    }
    if (-not (Start-DockerDesktop)) {
        return $false
    }
    Write-Info 'بانتظار جاهزية محرك Docker (قد يستغرق 1-3 دقائق)...' 'Waiting for the Docker engine (may take 1-3 minutes)...'
    for ($i = 0; $i -lt 90; $i++) {
        if (Test-DockerEngine) {
            Write-Info 'Docker أصبح جاهزًا.' 'Docker is now ready.'
            return $true
        }
        Start-Sleep -Seconds 2
    }
    Write-Info 'لم يصبح Docker جاهزًا في الوقت المتوقع — افتح Docker Desktop وأعد المحاولة.' 'Docker did not become ready in time - open Docker Desktop and retry.'
    return $false
}

try {
    if (-not (Test-Path -LiteralPath '.env')) {
        Write-Info 'ملف .env غير موجود — شغّل setup.bat أولًا.' '.env is missing - please run setup.bat first.'
        exit 1
    }
    Write-Section 'مرحبًا بك في تشغيل نظام ERP' 'ERP System - Start'
    if (-not (Wait-ForDocker)) {
        throw 'Docker is not available.'
    }
    Write-Section 'تشغيل الحاويات' 'Starting the containers'
    & docker compose up -d --build
    if ($LASTEXITCODE -ne 0) {
        throw 'docker compose up failed.'
    }

    Write-Section 'بانتظار جاهزية جميع الخدمات' 'Waiting for all services to become healthy'
    & docker compose up -d --wait --timeout 180
    if ($LASTEXITCODE -ne 0) {
        throw 'Services did not become healthy in time.'
    }

    Write-Section 'تسوية البيانات التجريبية (seed)' 'Seeding demo data (idempotent)'
    & docker compose exec -T web python -m scripts.seed

    Start-Process 'http://localhost:9009/'

    Write-Section 'النظام يعمل الآن' 'The system is running'
    Write-Host '   UI:      http://localhost:9009/'
    Write-Host '   Docs:    http://localhost:9009/api/v1/docs'
    Write-Host '   Health:  http://localhost:9009/health'
    Write-Host '   Login:   admin@example.com / admin123  (company: DEMO)'
    Write-Info 'تم فتح المتصفح تلقائيًا. لإيقاف البرنامج: docker compose down (لا يحذف البيانات).' 'Your browser was opened automatically. To stop: docker compose down (keeps your data).'
} catch {
    Write-Host ('[ERROR] ' + $_.Exception.Message) -ForegroundColor Red
    Write-Info 'شغّل setup.bat أولًا إذا كانت هذه أول مرة، أو راجع الأخطاء أعلاه.' 'Run setup.bat first if this is your first time, or check the errors above.'
} finally {
    Write-Host ''
    Invoke-Pause
}
