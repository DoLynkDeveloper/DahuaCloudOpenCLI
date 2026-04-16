@echo off
chcp 65001 >nul
:: Windows PATH 卸载脚本
:: 将 CLI 所在目录从用户 PATH 中移除

set "CLI_DIR=%~dp0"
set "CLI_DIR=%CLI_DIR:~0,-1%"

echo [INFO] 准备从 PATH 中移除以下目录:
echo %CLI_DIR%
echo.

:: 获取当前用户 PATH
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul ^| findstr /i "Path"') do set "USER_PATH=%%b"

:: 检查 PATH 是否存在
if not defined USER_PATH (
    echo [INFO] 用户 PATH 未设置，无需移除
    goto :end
)

:: 检查目录是否在 PATH 中
echo %USER_PATH% | find /i "%CLI_DIR%" >nul
if %errorlevel% neq 0 (
    echo [INFO] 目录不在 PATH 中，无需移除
    goto :end
)

:: 从 PATH 中移除该目录
:: 处理路径中的特殊字符，使用延迟扩展
setlocal enabledelayedexpansion
set "NEW_PATH=!USER_PATH:%CLI_DIR%;=!"
set "NEW_PATH=!NEW_PATH:;%CLI_DIR%=!"
set "NEW_PATH=!NEW_PATH:%CLI_DIR%=!"

:: 处理开头和结尾的分号
if "!NEW_PATH:~0,1!"==";" set "NEW_PATH=!NEW_PATH:~1!"
if "!NEW_PATH:~-1!"==";" set "NEW_PATH=!NEW_PATH:~0,-1!"

:: 更新 PATH
if "!NEW_PATH!"=="" (
    reg delete "HKCU\Environment" /v Path /f >nul 2>&1
    set "EXIT_CODE=!errorlevel!"
) else (
    setx Path "!NEW_PATH!" >nul 2>&1
    set "EXIT_CODE=!errorlevel!"
)

if "!EXIT_CODE!"=="0" (
    echo [SUCCESS] 已成功从 PATH 中移除
    echo.
    echo 请重新打开终端使更改生效
) else (
    echo [ERROR] 移除失败，错误代码: !EXIT_CODE!
)
endlocal

:end
echo.
pause
