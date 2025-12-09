@echo off
TITLE JCHEM Dashboard Installer
echo ===================================================
echo      INSTALLING JCHEM DASHBOARD & SHORTCUT
echo ===================================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed!
    echo Please install Python first from python.org.
    pause
    exit
)

:: 2. Install Requirements
echo [1/3] Installing required libraries...
pip install pandas plotly streamlit openpyxl altair

:: 3. Create Desktop Shortcut with Logo
echo [2/3] Creating Desktop Shortcut...
set SCRIPT="%TEMP%\CreateShortcut.vbs"

echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo sLinkFile = "%USERPROFILE%\Desktop\JCHEM Dashboard.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
:: IMPORTANT: This line tells the shortcut to look for RUNME.bat inside Jchemie
echo oLink.TargetPath = "%~dp0runme.bat" >> %SCRIPT%
echo oLink.WorkingDirectory = "%~dp0" >> %SCRIPT%
echo oLink.IconLocation = "%~dp0app_icon.ico" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%

cscript /nologo %SCRIPT%
del %SCRIPT%

echo [3/3] Installation Complete!
echo.
echo You can now find the "JCHEM Dashboard" icon on your Desktop.
pause