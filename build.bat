@echo off
chcp 65001 > nul
setlocal

echo ============================================
echo  打包 OBS 脚本编辑器
echo ============================================

set PYTHON=.venv\Scripts\python.exe

if not exist %PYTHON% (
    echo [错误] 找不到虚拟环境：%PYTHON%
    echo 请先创建虚拟环境：python -m venv .venv
    exit /b 1
)

echo [1/3] 检查 PyInstaller...
%PYTHON% -m pip show pyinstaller > nul 2>&1
if errorlevel 1 (
    echo [提示] 安装 PyInstaller...
    %PYTHON% -m pip install pyinstaller
)

echo [2/3] 清理旧构建...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [3/3] 开始打包...
%PYTHON% -m PyInstaller editor.spec --noconfirm

if errorlevel 1 (
    echo [错误] 打包失败
    exit /b 1
)

echo.
echo ============================================
echo  打包完成：dist\OBS脚本编辑器.exe
echo ============================================
echo.
echo 部署说明：
echo   1. 把 dist\OBS脚本编辑器.exe 复制到 obs-python-framework 目录下
echo   2. 确保同目录有 obsScriptFramework_ 子目录
echo   3. 双击运行即可
pause