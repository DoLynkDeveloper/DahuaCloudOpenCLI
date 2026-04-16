@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
:: Windows PATH 安装脚本
:: 将 CLI 所在目录添加到用户 PATH

set "CLI_DIR=%~dp0"
set "CLI_DIR=%CLI_DIR:~0,-1%"

echo [INFO] 准备将以下目录添加到 PATH:
echo !CLI_DIR!
echo.

:: 获取当前用户 PATH
set "USER_PATH="
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul ^| findstr /i "Path"') do set "USER_PATH=%%b"

:: 检查是否已安装在当前路径
echo !USER_PATH! | find /i "!CLI_DIR!" >nul
if !errorlevel! == 0 (
    echo [INFO] dahua-cloud CLI 已安装在此路径，无需重新安装:
    echo   !CLI_DIR!
    goto :end
)

:: 检查是否已安装在其他路径（PATH中包含dahua-cloud）
echo !USER_PATH! | find /i "dahua-cloud" >nul
if !errorlevel! == 0 (
    echo [WARNING] 检测到 dahua-cloud CLI 已安装在其他路径
    echo.
    set /p OVERWRITE="是否覆盖安装? (y/N): "
    if /i not "!OVERWRITE!"=="y" (
        echo [INFO] 已取消安装
        goto :end
    )
    echo [INFO] 正在移除旧条目...
    :: 遍历 PATH 条目，仅保留不含 dahua-cloud 的条目
    set "NEW_PATH="
    for %%p in ("!USER_PATH:;=" "!") do (
        set "ITEM=%%~p"
        if defined ITEM (
            echo !ITEM! | find /i "dahua-cloud" >nul
            if !errorlevel! neq 0 (
                if defined NEW_PATH (
                    set "NEW_PATH=!NEW_PATH!;!ITEM!"
                ) else (
                    set "NEW_PATH=!ITEM!"
                )
            )
        )
    )
    set "USER_PATH=!NEW_PATH!"
    echo [INFO] 继续安装...
    echo.
)

:: 添加到用户 PATH
if "!USER_PATH!"=="" (
    setx Path "!CLI_DIR!"
) else (
    setx Path "!USER_PATH!;!CLI_DIR!"
)

if !errorlevel! == 0 (
    echo [SUCCESS] 已成功添加到 PATH
    echo.
    echo 请重新打开终端，然后可以直接使用:
    echo   dahua-cloud image analysis --picture-url "URL" --prompt "描述"
) else (
    echo [ERROR] 添加失败，请以管理员权限运行
)

:end
endlocal
echo.
pause
