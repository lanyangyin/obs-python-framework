@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ============================================
echo  打包 OBS 脚本编辑器
echo ============================================

set PYTHON=.venv\Scripts\python.exe
set DIST=dist
set FRAMEWORK=obsScriptFramework_
set RELEASE_NAME=OBS脚本编辑器

if not exist %PYTHON% (
    echo [错误] 找不到虚拟环境：%PYTHON%
    echo 请先创建虚拟环境：python -m venv .venv
    exit /b 1
)

echo.
echo [1/5] 检查 PyInstaller...
%PYTHON% -m pip show pyinstaller > nul 2>&1
if errorlevel 1 (
    echo [提示] 安装 PyInstaller...
    %PYTHON% -m pip install pyinstaller
)

echo.
echo [2/5] 清理旧构建...
if exist build rmdir /s /q build
if exist %DIST% rmdir /s /q %DIST%

echo.
echo [3/5] 打包 exe...
%PYTHON% -m PyInstaller editor.spec --noconfirm
if errorlevel 1 (
    echo [错误] 打包失败
    exit /b 1
)

echo.
echo [4/5] 复制框架目录到发布包...
if not exist %FRAMEWORK% (
    echo [错误] 找不到 %FRAMEWORK% 目录
    exit /b 1
)
xcopy /E /I /Y /Q %FRAMEWORK% %DIST%\%FRAMEWORK%\ > nul
if errorlevel 1 (
    echo [错误] 复制 %FRAMEWORK% 失败
    exit /b 1
)

REM 生成 README
(
    echo OBS Script Framework 编辑器
    echo ============================
    echo.
    echo 使用方法：
    echo   1. 双击 OBS脚本编辑器.exe 启动
    echo   2. 编辑 obsScriptFramework_\plugins\widgetData.csv
    echo   3. 保存后可在 OBS 中重新加载脚本
    echo.
    echo 目录结构：
    echo   OBS脚本编辑器.exe        - 编辑器主程序
    echo   obsScriptFramework_\     - 框架目录（编辑器编辑的目标）
    echo   LOG\                     - 日志（自动生成）
    echo   editor_settings.json     - 用户设置（自动生成）
) > %DIST%\README.txt

REM 清理自动生成的文件，让 zip 干净
if exist %DIST%\LOG rmdir /s /q %DIST%\LOG
if exist %DIST%\editor_settings.json del /q %DIST%\editor_settings.json

echo.
echo [5/5] 生成 zip...
if exist "%DIST%\%RELEASE_NAME%.zip" del /q "%DIST%\%RELEASE_NAME%.zip"
powershell -NoProfile -Command "Compress-Archive -Path '%DIST%\*' -DestinationPath '%DIST%\%RELEASE_NAME%.zip' -Force"
if errorlevel 1 (
    echo [警告] 生成 zip 失败
)

echo.
echo ============================================
echo  打包完成！
echo ============================================
echo   exe:    %DIST%\OBS脚本编辑器.exe
echo   发布包: %DIST%\%RELEASE_NAME%.zip
echo.
echo   发布包内容：
dir /b %DIST%
echo.
pause