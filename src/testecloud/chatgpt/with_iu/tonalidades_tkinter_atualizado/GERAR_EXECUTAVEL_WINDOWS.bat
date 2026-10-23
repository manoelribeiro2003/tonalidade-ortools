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
echo       EMPACOTANDO TONALIDADES
echo ==========================================
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

REM Conferir a versao do Python selecionada pelo uv
echo Verificando Python do projeto...
uv run -- python -c "import sys; print('Python:', sys.version); print('Executavel:', sys.executable)"

if errorlevel 1 (
    echo ERRO: Nao foi possivel iniciar o Python do projeto.
    pause
    exit /b 1
)

REM Executar o PyInstaller com Python 3.13 ou superior
echo.
echo Iniciando o PyInstaller...

uv run --with pyinstaller -- python -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --windowed ^
    --onedir ^
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
echo Executavel em: dist\Tonalidades\Tonalidades.exe
echo ==========================================
echo.
pause

endlocal