@echo off
echo ============================================================
echo   CANSLIM Screener  ^|  FMP + Alpha Vantage + Yahoo Finance
echo ============================================================

set FMP_API_KEY=N1HukTVqzFwhSl1tpI13CVJh5cp0I29b
set AV_API_KEY=UMKP1E9TFZV1VNM6

cd /d "%~dp0"

echo.
echo [1/3] Running CANSLIM screener...
python canslim_screener.py --top 25 %*
if errorlevel 1 (
    echo ERROR: Screener failed.
    pause
    exit /b 1
)

echo.
echo [2/3] Updating index.html...
python update_html.py
if errorlevel 1 (
    echo ERROR: HTML update failed.
    pause
    exit /b 1
)

echo.
echo [3/3] サーバー起動 + ブラウザを開く...

:: ローカルIPを取得
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4" ^| findstr /v "169.254"') do (
    set LOCAL_IP=%%a
    goto :found
)
:found
set LOCAL_IP=%LOCAL_IP: =%

:: サーバーをバックグラウンドで起動（スマホからもアクセス可能）
start "" /b python -m http.server 5174 --directory "%~dp0" --bind 0.0.0.0

:: 少し待ってからブラウザを開く
timeout /t 2 /nobreak >nul
start "" http://localhost:5174

echo.
echo ============================================================
echo  PC用URL    : http://localhost:5174
echo  スマホ用URL : http://%LOCAL_IP%:5174
echo  (同じWiFiに接続したスマホのブラウザで上記URLを開いてください)
echo ============================================================
echo.
pause
