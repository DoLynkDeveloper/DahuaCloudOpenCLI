@echo off
chcp 65001 >nul
:: Windows PATH 安装脚本
:: 将 CLI 所在目录添加到用户 PATH

set "CLI_DIR=%~dp0"
set "CLI_DIR=%CLI_DIR:~0,-1%"

echo [INFO] 准备将以下目录添加到 PATH:
echo %CLI_DIR%
echo.

:: 获取当前用户 PATH
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul ^| findstr /i "Path"') do set "USER_PATH=%%b"

:: 检查是否已存在
if not defined USER_PATH (
    set "USER_PATH="
)

echo %USER_PATH% | find /i "%CLI_DIR%" >nul
if %errorlevel% == 0 (
    echo [INFO] 目录已在 PATH 中，无需添加
    goto :end
)

:: 添加到用户 PATH
if "%USER_PATH%"=="" (
    setx Path "%CLI_DIR%"
) else (
    setx Path "%USER_PATH%;%CLI_DIR%"
)

if %errorlevel% == 0 (
    echo [SUCCESS] 已成功添加到 PATH
    echo.
    echo 请重新打开终端，然后可以直接使用:
    echo   dahua-cloud image analysis --picture-url "URL" --prompt "描述"
) else (
    echo [ERROR] 添加失败，请以管理员权限运行
)

:end
echo.
pause
