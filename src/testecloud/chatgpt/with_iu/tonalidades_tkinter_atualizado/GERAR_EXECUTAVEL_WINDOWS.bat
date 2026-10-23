@echo off
setlocal

title Build - Tonalidades

REM Ir para a raiz do projeto
cd /d "%~dp0"

REM Caminhos da aplicacao
set "APP_DIR=C:\Users\ml0559\Desktop\Projetos\python\tonalidade-ortools\src\testecloud\chatgpt\with_iu\tonalidades_tkinter_atualizado"
set "ENTRY=%APP_DIR%\tonalidades_tkinter.py"
set "ALGORITHM=%APP_DIR%\divisao_tonalidades_ergonomico.py"

echo.
echo ==========================================
echo        BUILD - TONALIDADES
echo ==========================================
echo.
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

REM Verificar se os arquivos existem
if not exist "%ENTRY%" (
    echo ERRO: Arquivo principal nao encontrado:
    echo %ENTRY%
    pause
    exit /b 1
)

if not exist "%ALGORITHM%" (
    echo ERRO: Algoritmo nao encontrado:
    echo %ALGORITHM%
    pause
    exit /b 1
)

REM Verificar o Python do projeto
echo Verificando Python selecionado pelo uv...

uv run -- python -c "import sys; print('Python:', sys.version); print('Executavel:', sys.executable)"

if errorlevel 1 (
    echo.
    echo ERRO: Nao foi possivel iniciar o Python do projeto.
    pause
    exit /b 1
)

REM Executar o PyInstaller
echo.
echo Iniciando o PyInstaller...
echo.

uv run --with pyinstaller -- python -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --windowed ^
    %MODO% ^
    --name Tonalidades ^
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

echo.
echo ==========================================
echo BUILD CONCLUIDO!
echo ==========================================
echo.

if "%OPCAO%"=="1" (
    echo Executavel: dist\Tonalidades\Tonalidades.exe
    echo.
    echo IMPORTANTE: Distribua a pasta Tonalidades inteira.
) else (
    echo Executavel: dist\Tonalidades.exe
    echo.
    echo O aplicativo foi empacotado em um unico arquivo.
)

echo.
pause

endlocal