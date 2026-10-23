# Como gerar o build do Tonalidades

Este documento explica como empacotar o aplicativo Tonalidades para
Windows usando `uv` e PyInstaller.

## Pré-requisitos

-   Execute os comandos na raiz do projeto, onde ficam `pyproject.toml`
    e `.python-version`.
-   Tenha o `uv` instalado.
-   Os comandos abaixo consideram esta estrutura:

``` text
src/
└── testecloud/
    └── chatgpt/
        └── with_iu/
            └── tonalidades_tkinter_atualizado/
                ├── tonalidades_tkinter.py
                └── divisao_tonalidades_ergonomico.py
```

Se os nomes ou caminhos dos arquivos forem diferentes, ajuste os
comandos.

## 1. Verificar o Python do projeto

Na raiz do projeto, execute:

``` cmd
uv run -- python -c "import sys; print(sys.version); print(sys.executable)"
```

O `uv` deve selecionar uma versão compatível com a configuração do
projeto, incluindo `requires-python = ">=3.13"` e `.python-version`.

## 2. Escolher o formato de distribuição

-   **`onedir`**: gera um executável acompanhado dos arquivos de
    suporte. Distribua a pasta inteira, não apenas o `.exe`.
-   **`onefile`**: gera um único `.exe` que contém o aplicativo e suas
    dependências. A inicialização pode demorar mais porque os arquivos
    de suporte são extraídos temporariamente.

## 3. Gerar o build em modo `onedir`

Execute na raiz do projeto:

``` cmd
uv run --with pyinstaller -- python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --onedir ^
  --name Tonalidades ^
  --collect-all ortools ^
  --hidden-import ortools.sat.python.cp_model ^
  --add-data "src\testecloud\chatgpt\with_iu\tonalidades_tkinter_atualizado\divisao_tonalidades_ergonomico.py;." ^
  "src\testecloud\chatgpt\with_iu\tonalidades_tkinter_atualizado\tonalidades_tkinter.py"
```

Resultado esperado:

``` text
dist/
└── Tonalidades/
    ├── Tonalidades.exe
    └── _internal/
        └── ...
```

Para distribuir essa versão, compacte e compartilhe a pasta
`dist\Tonalidades` inteira.

## 4. Gerar o build em modo `onefile`

Execute na raiz do projeto:

``` cmd
uv run --with pyinstaller -- python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --onefile ^
  --name Tonalidades ^
  --collect-all ortools ^
  --hidden-import ortools.sat.python.cp_model ^
  --add-data "src\testecloud\chatgpt\with_iu\tonalidades_tkinter_atualizado\divisao_tonalidades_ergonomico.py;." ^
  "src\testecloud\chatgpt\with_iu\tonalidades_tkinter_atualizado\tonalidades_tkinter.py"
```

Resultado esperado:

``` text
dist/
└── Tonalidades.exe
```

## 5. Testar o executável

1.  Execute o `.exe` gerado.
2.  Confirme que a interface abre e que as funções de otimização
    funcionam.
3.  Para testar a distribuição, copie os arquivos gerados para outra
    pasta ou para um computador Windows de destino.
4.  No modo `onedir`, mantenha `_internal` e os demais arquivos junto ao
    executável.

> **Importante:** o arquivo `divisao_tonalidades_ergonomico.py` é
> incluído como dado porque a interface pode carregá-lo dinamicamente. O
> código da interface precisa localizar esse arquivo corretamente quando
> estiver empacotado. Se ocorrer erro ao localizar o algoritmo no modo
> `onefile`, será necessário ajustar a resolução do caminho no código da
> aplicação.

## 6. Publicar no GitHub

Para distribuir o aplicativo, publique o artefato em **GitHub
Releases**:

-   No modo `onefile`, anexe `dist\Tonalidades.exe`.
-   No modo `onedir`, compacte a pasta `dist\Tonalidades` em um arquivo
    ZIP e anexe o ZIP.

Não inclua `.venv`, `build` ou arquivos temporários do PyInstaller no
pacote de distribuição.
