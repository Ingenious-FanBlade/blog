@echo off
rem ============================================================
rem  gif2avif 启动器：自动挑选一个带 AVIF 编码能力的 Python
rem  用法：gif2avif.cmd 输入.gif [-o 输出.avif] [其他参数]
rem  也可用环境变量指定解释器：set GIF2AVIF_PYTHON=C:\path\python.exe
rem ============================================================
setlocal
chcp 65001 >nul 2>&1
set "SCRIPT=%~dp0gif2avif.py"
set "PY="

if not exist "%SCRIPT%" (
  echo [gif2avif] 找不到 gif2avif.py（应与本 .cmd 放在同一目录）
  exit /b 2
)

rem 1) 用户指定
if defined GIF2AVIF_PYTHON call :try_exe "%GIF2AVIF_PYTHON%"

rem 2) PATH 里的 python / py 启动器
call :try_cmd python
call :try_cmd py -3.10
call :try_cmd py -3.11
call :try_cmd py -3.12
call :try_cmd py -3.13

rem 3) 常见的 conda / miniconda 环境
for /d %%D in ("%USERPROFILE%\miniconda3\envs\*") do call :try_exe "%%~fD\python.exe"
for /d %%D in ("%USERPROFILE%\anaconda3\envs\*") do call :try_exe "%%~fD\python.exe"
for /d %%D in ("C:\ProgramData\miniconda3\envs\*") do call :try_exe "%%~fD\python.exe"
for /d %%D in ("C:\ProgramData\anaconda3\envs\*") do call :try_exe "%%~fD\python.exe"
for /d %%D in ("C:\miniconda3\envs\*") do call :try_exe "%%~fD\python.exe"
for /d %%D in ("D:\miniconda3\envs\*") do call :try_exe "%%~fD\python.exe"

if not defined PY (
  echo [gif2avif] 没有找到支持 AVIF 的 Python，需要 Pillow ^>= 11.3：
  echo             pip install -U "pillow>=11.3"
  echo             或用环境变量指定：set GIF2AVIF_PYTHON=C:\path\to\python.exe
  exit /b 2
)

%PY% "%SCRIPT%" %*
exit /b %ERRORLEVEL%

rem ---- 尝试无空格的命令（python / py -3.x） ----
:try_cmd
if defined PY exit /b 0
if "%~1"=="" exit /b 0
%~1 -c "import sys;from PIL import features;sys.exit(0 if features.check('avif') else 1)" >nul 2>&1
if errorlevel 1 exit /b 0
set "PY=%~1"
echo [gif2avif] 使用 Python: %~1
exit /b 0

rem ---- 尝试解释器的完整路径（可能含空格） ----
:try_exe
if defined PY exit /b 0
if not exist "%~1" exit /b 0
"%~1" -c "import sys;from PIL import features;sys.exit(0 if features.check('avif') else 1)" >nul 2>&1
if errorlevel 1 exit /b 0
set PY="%~1"
echo [gif2avif] 使用 Python: %~1
exit /b 0
