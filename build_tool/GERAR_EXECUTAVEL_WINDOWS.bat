@echo off
setlocal

title Build - Tonalidades

REM ==================================================
REM CONFIGURACAO DOS CAMINHOS
REM ==================================================

REM Raiz do projeto: pasta acima de build_tool
for %%I in ("%~dp0..") do set "PROJECT_DIR=%%~fI"

REM Diretórios do projeto
set "APP_DIR=%PROJECT_DIR%\src"
set "DIST_DIR=%PROJECT_DIR%\dist"
set "BUILD_DIR=%PROJECT_DIR%\build"
set "SPEC_DIR=%PROJECT_DIR%\build_tool"

REM Arquivos da aplicação
set "ENTRY=%APP_DIR%\tonalidades_tkinter.py"
set "ALGORITHM=%APP_DIR%\divisao_tonalidades_ergonomico.py"

REM Entrar na raiz do projeto
cd /d "%PROJECT_DIR%" || (
    echo ERRO: Nao foi possivel acessar a raiz do projeto.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo           BUILD - TONALIDADES
echo ==========================================
echo.
echo Raiz do projeto: %PROJECT_DIR%
echo Saida dos executaveis: %DIST_DIR%
echo.

REM ==================================================
REM SELECAO DO FORMATO
REM ==================================================

echo Escolha o formato do executavel:
echo.
echo [1] onedir  - Executavel com pasta de suporte
echo [2] onefile - Executavel unico
echo.

set /p "OPCAO=Digite sua opcao (1 ou 2): "

if "%OPCAO%"=="1" (
    set "MODO=--onedir"
    set "FORMATO=onedir"
) else if "%OPCAO%"=="2" (
    set "MODO=--onefile"
    set "FORMATO=onefile"
) else (
    echo.
    echo ERRO: Opcao invalida.
    pause
    exit /b 1
)

echo.
echo Formato selecionado: %FORMATO%
echo.

REM ==================================================
REM VALIDACAO DOS ARQUIVOS
REM ==================================================

if not exist "%ENTRY%" (
    echo ERRO: Arquivo principal nao encontrado:
    echo "%ENTRY%"
    pause
    exit /b 1
)

if not exist "%ALGORITHM%" (
    echo ERRO: Algoritmo nao encontrado:
    echo "%ALGORITHM%"
    pause
    exit /b 1
)

REM ==================================================
REM VALIDACAO DO PYTHON / UV
REM ==================================================

where uv >nul 2>&1

if errorlevel 1 (
    echo ERRO: O comando uv nao foi encontrado no PATH.
    pause
    exit /b 1
)

echo Verificando Python selecionado pelo uv...
echo.

uv run -- python -c "import sys; print('Python:', sys.version); print('Executavel:', sys.executable)"

if errorlevel 1 (
    echo.
    echo ERRO: Nao foi possivel iniciar o Python do projeto.
    pause
    exit /b 1
)

REM ==================================================
REM PREPARAR DIRETORIOS
REM ==================================================

if not exist "%DIST_DIR%" mkdir "%DIST_DIR%"
if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"

if errorlevel 1 (
    echo ERRO: Nao foi possivel preparar os diretorios.
    pause
    exit /b 1
)

REM ==================================================
REM EXECUTAR O PYINSTALLER
REM ==================================================

echo.
echo Iniciando o PyInstaller...
echo.

uv run --with pyinstaller -- python -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --windowed ^
    %MODO% ^
    --name Tonalidades ^
    --distpath "%DIST_DIR%" ^
    --workpath "%BUILD_DIR%" ^
    --specpath "%SPEC_DIR%" ^
    --collect-all ortools ^
    --hidden-import ortools.sat.python.cp_model ^
    --add-data "%ALGORITHM%;." ^
    "%ENTRY%"

if errorlevel 1 (
    echo.
    echo ERRO: O empacotamento falhou.
    pause
    exit /b 1
)

REM ==================================================
REM RESULTADO
REM ==================================================

echo.
echo ==========================================
echo             BUILD CONCLUIDO!
echo ==========================================
echo.

if "%OPCAO%"=="1" (
    echo Executavel:
    echo "%DIST_DIR%\Tonalidades\Tonalidades.exe"
    echo.
    echo IMPORTANTE: Distribua a pasta Tonalidades inteira.
) else (
    echo Executavel:
    echo "%DIST_DIR%\Tonalidades.exe"
    echo.
    echo O aplicativo foi empacotado em um unico arquivo.
)

echo.
pause

endlocal