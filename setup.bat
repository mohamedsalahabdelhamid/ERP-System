@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$f='%~f0'; $o=Join-Path $env:TEMP 'erp_setup.ps1'; $l=Get-Content -LiteralPath $f -Encoding UTF8; $i=($l | Select-String '^@@@PS@@@$' | Select-Object -First 1).LineNumber - 1; $l[($i + 1)..($l.Count - 1)] | Set-Content -LiteralPath $o -Encoding UTF8; & $o; Remove-Item -LiteralPath $o -ErrorAction SilentlyContinue"
goto :EOF
@@@PS@@@
$ErrorActionPreference = 'Continue'

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
        Write-Info 'Docker Desktop غير مثبّت. جارٍ محاولة التثبيت عبر winget...' 'Docker Desktop not found - trying winget install...'
        if (Get-Command winget -ErrorAction SilentlyContinue) {
            winget install -e --id Docker.DockerDesktop --accept-package-agreements --accept-source-agreements | Out-Host
            $exe = $paths | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
        }
        if (-not $exe) {
            Write-Info 'من فضلك ثبّت Docker Desktop يدويًا: https://www.docker.com/products/docker-desktop/ ثم أعد تشغيل هذا الملف.' 'Please install Docker Desktop manually: https://www.docker.com/products/docker-desktop/ then re-run this file.'
            return $false
        }
    }
    Write-Info 'جارٍ فتح Docker Desktop...' 'Starting Docker Desktop...'
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
    Write-Info 'لم يصبح Docker جاهزًا في الوقت المتوقع. افتح Docker Desktop وأعد تشغيل الملف.' 'Docker did not become ready in time. Open Docker Desktop and re-run this file.'
    return $false
}

function New-RandomString([int]$Length) {
    $rng = New-Object System.Security.Cryptography.RNGCryptoServiceProvider
    $bytes = New-Object byte[] $Length
    $rng.GetBytes($bytes)
    $rng.Dispose()
    $chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    $sb = New-Object System.Text.StringBuilder
    foreach ($b in $bytes) {
        [void]$sb.Append($chars[$b % $chars.Length])
    }
    return $sb.ToString()
}

try {
    Write-Section 'مرحبًا بك في تجهيز نظام ERP' 'ERP System - Setup'
    Write-Info 'يجهّز هذا الملف كل شيء تلقائيًا (متكرر وآمن — يمكنك تشغيله أكثر من مرة).' 'This file prepares everything automatically (idempotent and safe to re-run).'

    if (-not (Wait-ForDocker)) {
        Write-Info 'لا يمكن المتابعة بدون Docker.' 'Cannot continue without Docker.'
    } else {
        # --- .env ---
        Write-Section 'إعداد ملف .env' 'Preparing the .env file'
        if (-not (Test-Path -LiteralPath '.env')) {
            Copy-Item -LiteralPath '.env.example' -Destination '.env'
            $content = Get-Content -LiteralPath '.env' -Raw
            $content = $content.Replace('change-me-in-production-please-use-a-long-random-string', (New-RandomString 32))
            $content = $content.Replace('erp_password_change_me', (New-RandomString 24))
            $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
            [System.IO.File]::WriteAllText((Join-Path (Get-Location) '.env'), $content, $utf8NoBom)
            Write-Info 'تم إنشاء .env بمفتاح سري وكلمة مرور عشوائية آمنة.' '.env created with a random SECRET_KEY and POSTGRES_PASSWORD.'
        } else {
            Write-Info '.env موجود مسبقًا — لم يتم تغييره (لحماية بيانات قاعدة البيانات).' '.env already exists - left untouched to protect the database volume.'
        }

        # --- Docker images ---
        Write-Section 'بناء صور Docker (يثبّت المتطلبات داخل الحاويات)' 'Building Docker images (installs requirements inside containers)'
        Write-Info 'قد يستغرق ذلك عدة دقائق في أول مرة.' 'This may take a few minutes on first run.'
        & docker compose build
        if ($LASTEXITCODE -eq 0) {
            Write-Info 'تم بناء الصور بنجاح.' 'Images built successfully.'
        } else {
            Write-Info 'فشل بناء الصور — راجع الرسائل أعلاه.' 'Image build failed - see the messages above.'
        }

        # --- Local Python environment (for tests) ---
        $py = Get-Command python -ErrorAction SilentlyContinue
        if ($py) {
            if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
                Write-Section 'إنشاء بيئة Python المحلية' 'Creating the local Python environment'
                python -m venv .venv
            }
            # Install requirements only on first setup; reuse a working venv.
            & .\.venv\Scripts\python.exe -c "import fastapi, pydantic, pytest" 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Info 'بيئة الاختبارات المحلية جاهزة مسبقًا (تم التخطي).' 'Local test environment already provisioned (skipped).'
            } else {
                Write-Section 'تثبيت متطلبات الاختبارات (requirements.txt)' 'Installing test requirements (requirements.txt)'
                & .\.venv\Scripts\python.exe -m pip install -r requirements.txt
                if ($LASTEXITCODE -ne 0) {
                    Write-Info 'تعذّر تثبيت بعض المتطلبات محليًا (غالبًا بسبب نسخة Python) — لن يمنع ذلك تشغيل البرنامج عبر Docker.' 'Some requirements could not be installed locally (likely a Python version issue) - the Docker-based app will still run.'
                }
            }
        } else {
            Write-Info 'Python غير موجود — تخطي البيئة المحلية (النظام يعمل عبر Docker على أي حال).' 'Python not found - skipping the local env (the app runs via Docker anyway).'
        }

        # --- Frontend local deps (optional, for dev) ---
        if (Get-Command node -ErrorAction SilentlyContinue) {
            if (-not (Test-Path -LiteralPath 'frontend\node_modules')) {
                Write-Section 'تثبيت متطلبات الواجهة (npm install)' 'Installing frontend dependencies (npm install)'
                Push-Location 'frontend'
                npm install
                Pop-Location
            } else {
                Write-Info 'متطلبات الواجهة موجودة مسبقًا (frontend\node_modules).' 'Frontend dependencies already present (frontend\node_modules).'
            }
        } else {
            Write-Info 'Node غير موجود — تخطي npm (الواجهة تُبنى داخل Docker تلقائيًا).' 'Node not found - skipping npm (the frontend builds inside Docker).'
        }

        # --- Tests ---
        if ($py -and (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
            Write-Section 'تشغيل الاختبارات' 'Running the test suite'
            & .\.venv\Scripts\python.exe -m pytest -q
            if ($LASTEXITCODE -eq 0) {
                Write-Host '[OK] كل الاختبارات ناجحة.' -ForegroundColor Green
            } else {
                Write-Host '[!] بعض الاختبارات فشلت — راجع التفاصيل أعلاه (لا يمنع تشغيل البرنامج).' -ForegroundColor Yellow
            }
        }

        Write-Section 'اكتمل التجهيز' 'Setup complete'
        Write-Info 'الآن انقر مرتين على الملف الثاني: start.bat' 'Now double-click the second file: start.bat'
        Write-Info 'أو يدويًا: docker compose up -d' 'Or manually: docker compose up -d'
    }
} catch {
    Write-Host ('[ERROR] ' + $_.Exception.Message) -ForegroundColor Red
} finally {
    Write-Host ''
    Invoke-Pause
}
