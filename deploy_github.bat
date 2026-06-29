@echo off
:: ============================================================
::  GitHub Pages デプロイスクリプト
::  初回: deploy_github.bat setup YOUR_GITHUB_USERNAME
::  毎回: deploy_github.bat
:: ============================================================
setlocal

cd /d "%~dp0"

if "%1"=="setup" goto :SETUP

:: ── 通常デプロイ（スクリーニング後に実行）────────────────────
echo [デプロイ] index.html を GitHub Pages にプッシュ...
git add index.html screening_results.json
git commit -m "Update screening results %date% %time%"
git push origin main
echo.
echo デプロイ完了！数分後に以下のURLでアクセスできます：
for /f %%i in ('git remote get-url origin') do set REMOTE=%%i
echo   https://[あなたのユーザー名].github.io/canslim-screener/
pause
goto :EOF

:: ── 初回セットアップ ───────────────────────────────────────
:SETUP
set GITHUB_USER=%2
if "%GITHUB_USER%"=="" (
    set /p GITHUB_USER="GitHubユーザー名を入力: "
)

echo [初回セットアップ] GitHubリポジトリと接続...

:: git初期化
git init
git add .
git commit -m "Initial: CANSLIM/SMART Screener"
git branch -M main

echo.
echo 次の手順を実行してください：
echo.
echo  1. https://github.com/new を開く
echo  2. Repository name: canslim-screener
echo  3. Public を選択（Pages使用のため）
echo  4. "Create repository" をクリック
echo  5. このウィンドウに戻って Enter を押す
echo.
pause

git remote add origin https://github.com/%GITHUB_USER%/canslim-screener.git
git push -u origin main

echo.
echo  6. GitHubリポジトリの Settings タブを開く
echo  7. Pages → Source → Deploy from branch
echo  8. Branch: main / folder: / (root) → Save
echo.
echo 数分後に以下のURLが有効になります：
echo   https://%GITHUB_USER%.github.io/canslim-screener/
echo.
pause
