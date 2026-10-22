"""
Divisão de tonalidades v2 (Google OR-Tools, CP-SAT)

Modelo de otimização por batidas físicas inteiras.

- Cada fileira representa uma combinação de navalhas de um único componente.
- O CP-SAT escolhe uma tonalidade única para cada tamanho, compartilhada pelos
  tipos de componente, e a quantidade inteira de batidas de cada fileira/tom.
- Cada batida consome o comprimento físico máximo das navalhas da fileira,
  acrescido do adicional configurado para o tipo (0,3 cm para as gaspeas).
- A largura ocupada respeita a largura útil da mesa (139 - 1 = 138 cm).
- O rendimento de produção desconta PERC_TROCAS (1%) como no modelo anterior.
- O estoque de cada tom é compartilhado entre todos os componentes cortados.
- A função objetivo minimiza o consumo total de tecido.

Execução: python divisao_tonalidades_v2.py
Autoteste das fórmulas antigas: python divisao_tonalidades_v2.py --teste
"""

import json
import sys
import math
from itertools import combinations, product

# ---------------------------------------------------------------------------
# 1) PARÂMETROS GERAIS
# ---------------------------------------------------------------------------

ESCALA = 100  # cm -> centésimos de cm (tudo em inteiros)
METRO = 100 * ESCALA  # 1 metro em centésimos de cm


def cm(valor: float) -> int:
    return round(valor * ESCALA)


def componentes_por_batida(pares: float) -> int:
    """Converte 'pares por batida' em componentes (1 par = 2 componentes).
    0.5 -> 1 componente por batida | 1 -> 1 par (2 componentes) | 2 -> 2 pares (4 componentes)."""
    comp = round(pares * 2)
    if comp < 1 or abs(comp - pares * 2) > 1e-9:
        raise ValueError(f"'pares' deve ser múltiplo de 0,5 (recebido: {pares})")
    return comp


LARGURA_MESA = cm(139.0)
MARGEM_SEGURANCA = cm(1.0)  # regra prioritária: fileira de 139 é inválida, até 138 vale
FOLGA_ENTRE_NAVALHAS = cm(0.0)  # não é regra absoluta; 0 por padrão
ACRESCIMO_COMPRIMENTO = cm(0.4)  # planilha: 0,4 cm (0,3 cm na navalha quadrada)
PERC_TROCAS = 1  # % de perda por trocas (planilha: 1%; versões antigas 2%; meia 5%)
MAX_TAMANHOS_POR_FILEIRA = 2  # por enquanto combinamos até dois tamanhos
TEMPO_LIMITE_S = 60

# ---------------------------------------------------------------------------
# 2) DADOS DE EXECUÇÃO
# ---------------------------------------------------------------------------
# O algoritmo não contém demanda, navalhas ou estoque padrão.
# Esses dados são recebidos por resolver(configuracao), normalmente enviados
# pela interface gráfica. As variáveis abaixo só são preenchidas durante uma execução.
TIPOS = {}
NAVALHAS = {}
PARES_POR_TAMANHO = {}
COMPONENTES = []
TONS_METROS = {}


def navalha(largura1, comprimento1, pares=1, largura2=None, comprimento2=None):
    """Cria uma navalha a partir de medidas em centímetros."""
    componentes_por_batida(pares)
    return {
        "largura1": cm(largura1),
        "largura2": cm(largura2) if largura2 is not None else cm(largura1),
        "comprimento1": cm(comprimento1),
        "comprimento2": cm(comprimento2) if comprimento2 is not None else None,
        "pares": pares,
    }


# ---------------------------------------------------------------------------
# 3) FÓRMULAS DA PLANILHA (funções puras, todas em inteiros)
# ---------------------------------------------------------------------------


def batidas_largura_encaixe(largura1: int, largura2: int, largura_seq: int) -> int:
    """Planilha: ROUNDDOWN((Larg.Seq - Larg1) / Larg2 + 1, 0)."""
    if largura_seq < largura1:
        return 0
    return (largura_seq - largura1) // largura2 + 1


def fileiras_por_metro_encaixe_100(comprimento1: int, comprimento2: int) -> int:
    """Planilha: ROUNDDOWN((100 - Comp1) / Comp2 + 1, 2), em centésimos."""
    return 100 + (100 * (METRO - comprimento1)) // comprimento2


def fileiras_por_metro_simples_100(comprimento: int, acrescimo: int) -> int:
    """Planilha: ROUNDDOWN(100 / (Comp + acréscimo), 2), em centésimos."""
    return (100 * METRO) // (comprimento + acrescimo)


def consumo_100(
    batidas: int, pares: float, fileiras_metro_100: int, perc_trocas: int
) -> int:
    """Consumo em CENTÉSIMOS de pares/m: batidas x pares/nav x fileiras/m x (100-% trocas)/100.
    Cálculo em inteiros (via componentes) para o CP-SAT aceitar os coeficientes.
    [SUPOSIÇÃO para fileiras com mais de um tamanho: ver cabeçalho.]"""
    comp = componentes_por_batida(pares)
    return batidas * comp * fileiras_metro_100 * (100 - perc_trocas) // 200


# ---------------------------------------------------------------------------
# 4) GERAÇÃO DAS FILEIRAS (geometria)
# ---------------------------------------------------------------------------


def _nav(tipo, tamanho):
    return NAVALHAS[(tipo, tamanho)]


def largura_fileira(tipo: str, contagem: dict):
    """Retorna (largura ocupada, tamanho que fica à esquerda).
    Encaixe: largura = soma das larguras 2 + (largura1 - largura2) de quem fica na primeira posição.
    Como só o primeiro usa a largura 1, escolhemos à esquerda o tamanho de menor (L1 - L2)."""
    total = sum(contagem.values())
    folgas = FOLGA_ENTRE_NAVALHAS * (total - 1)
    if TIPOS[tipo]["encaixe"]:
        soma_l2 = sum(n * _nav(tipo, t)["largura2"] for t, n in contagem.items())
        primeiro = min(
            contagem,
            key=lambda t: _nav(tipo, t)["largura1"] - _nav(tipo, t)["largura2"],
        )
        ganho = _nav(tipo, primeiro)["largura1"] - _nav(tipo, primeiro)["largura2"]
        return soma_l2 + ganho + folgas, primeiro
    soma = sum(n * _nav(tipo, t)["largura1"] for t, n in contagem.items())
    return soma + folgas, None


def fileiras_por_metro_100(tipo: str, tamanhos) -> int:
    navs = [_nav(tipo, t) for t in tamanhos]
    if all(n["comprimento2"] is not None for n in navs):
        c1 = max(n["comprimento1"] for n in navs)
        c2 = max(n["comprimento2"] for n in navs)
        return fileiras_por_metro_encaixe_100(c1, c2)
    acr = TIPOS[tipo].get("acrescimo_comprimento", ACRESCIMO_COMPRIMENTO)
    return fileiras_por_metro_simples_100(max(n["comprimento1"] for n in navs), acr)


def comprimento_batida_100(tipo: str, contagem: dict) -> int:
    """Comprimento físico da batida (maior navalha) + adicional do tipo, em 0,01 cm."""
    maior_comprimento = max(
        _nav(tipo, tamanho)["comprimento1"] for tamanho in contagem
    )
    adicional = TIPOS[tipo].get("acrescimo_comprimento", ACRESCIMO_COMPRIMENTO)
    return maior_comprimento + adicional


def gerar_fileiras(tipo: str, tamanhos: list) -> list:
    limite = LARGURA_MESA - MARGEM_SEGURANCA
    encaixe = TIPOS[tipo]["encaixe"]
    menor = min(
        (_nav(tipo, t)["largura2"] if encaixe else _nav(tipo, t)["largura1"])
        for t in tamanhos
    )
    max_bat = limite // menor

    fileiras = []
    for k in range(1, MAX_TAMANHOS_POR_FILEIRA + 1):
        for combo in combinations(tamanhos, k):
            for contagens in product(range(1, max_bat + 1), repeat=k):
                contagem = dict(zip(combo, contagens))
                largura, primeiro = largura_fileira(tipo, contagem)
                if largura > limite:
                    continue
                comprimento = comprimento_batida_100(tipo, contagem)
                fileiras.append(
                    {
                        "tipo": tipo,
                        "contagem": contagem,
                        "esquerda": primeiro,
                        "largura": largura,
                        "comprimento_batida_100": comprimento,
                    }
                )
    return fileiras


def descrever(f: dict) -> str:
    partes = [f"{n}x{t}" for t, n in f["contagem"].items()]
    return " + ".join(partes) + f"  (larg. {f['largura'] / ESCALA:.2f} cm)"


def validar_dados() -> None:
    for tipo in COMPONENTES:
        assert tipo in TIPOS, f"Tipo sem cadastro: {tipo}"
        for tam in PARES_POR_TAMANHO:
            assert (tipo, tam) in NAVALHAS, f"Falta a navalha {tipo} {tam}"
            n = NAVALHAS[(tipo, tam)]
            if TIPOS[tipo]["encaixe"]:
                assert n["largura2"] <= n["largura1"], (
                    f"Largura 2 deve ser <= largura 1 ({tipo} {tam})"
                )


# ---------------------------------------------------------------------------
# 5) BLOCOS DE PRODUÇÃO ERGONÔMICOS
# ---------------------------------------------------------------------------


def teto_div(a: float, b: float) -> int:
    """ceil(a / b), protegendo contra pequenas imprecisões de ponto flutuante."""
    return math.ceil(a / b - 1e-9)


def alvo_bruto(tamanho: str) -> int:
    """Pares brutos necessários para cobrir a demanda após PERC_TROCAS de perda."""
    return teto_div(PARES_POR_TAMANHO[tamanho] * 100, 100 - PERC_TROCAS)


def max_navalhas_largura(tipo: str, tamanho: str) -> int:
    limite = LARGURA_MESA - MARGEM_SEGURANCA
    largura = _nav(tipo, tamanho)["largura2"] if TIPOS[tipo]["encaixe"] else _nav(tipo, tamanho)["largura1"]
    return max(0, limite // (largura + FOLGA_ENTRE_NAVALHAS))


def largura_simples(tipo: str, tamanho: str, quantidade: int) -> int:
    largura, _ = largura_fileira(tipo, {tamanho: quantidade})
    return largura


def criar_etapa(tipo: str, contagem: dict, batidas_qtd: int) -> dict:
    """Cria uma etapa física, com batidas inteiras e produção bruta por tamanho."""
    comprimento = comprimento_batida_100(tipo, contagem)
    largura, esquerda = largura_fileira(tipo, contagem)
    pares_por_batida = {
        s: contagem[s] * _nav(tipo, s)["pares"] for s in contagem
    }
    return {
        "contagem": dict(contagem),
        "descricao": descrever({"contagem": contagem, "largura": largura}),
        "esquerda": esquerda,
        "largura_100": largura,
        "batidas": batidas_qtd,
        "comprimento_100": comprimento,
        "consumo_100": batidas_qtd * comprimento,
        "pares_por_batida": pares_por_batida,
        "pares_brutos": {s: batidas_qtd * p for s, p in pares_por_batida.items()},
    }


def finalizar_bloco(tipo: str, tamanhos: tuple, etapas: list) -> dict:
    producao = {s: 0.0 for s in tamanhos}
    consumo = 0
    for etapa in etapas:
        consumo += etapa["consumo_100"]
        for s, qtd in etapa["pares_brutos"].items():
            producao[s] += qtd
    return {
        "tipo": tipo,
        "tamanhos": tuple(tamanhos),
        "etapas": etapas,
        "consumo_100": consumo,
        "producao_bruta": producao,
    }


def gerar_blocos(tipo: str, tamanhos: list[str]) -> list[dict]:
    """Gera campanhas completas.

    Um bloco pode ser:
      - um tamanho sozinho até completar sua demanda; ou
      - dois tamanhos combinados até um deles completar, seguido imediatamente
        pelo tamanho ainda pendente sozinho.

    Cada tamanho pertence a exatamente um bloco por tipo de gaspea. Assim ele
    não pode ser repartido entre combinações diferentes, mas pode continuar
    sozinho como segunda etapa da mesma campanha se o parceiro terminar antes.
    """
    limite = LARGURA_MESA - MARGEM_SEGURANCA
    blocos = []
    alvos = {s: alvo_bruto(s) for s in tamanhos}

    # Campanhas de um único tamanho.
    for s in tamanhos:
        max_qtd = max_navalhas_largura(tipo, s)
        for qtd in range(1, max_qtd + 1):
            contagem = {s: qtd}
            largura, _ = largura_fileira(tipo, contagem)
            if largura > limite:
                continue
            pares_batida = qtd * _nav(tipo, s)["pares"]
            n_batidas = teto_div(alvos[s], pares_batida)
            etapa = criar_etapa(tipo, contagem, n_batidas)
            blocos.append(finalizar_bloco(tipo, (s,), [etapa]))

    # Campanhas iniciadas com dois tamanhos. Não se combinam mais de dois.
    for s1, s2 in combinations(tamanhos, 2):
        max1 = max_navalhas_largura(tipo, s1)
        max2 = max_navalhas_largura(tipo, s2)
        for q1 in range(1, max1 + 1):
            for q2 in range(1, max2 + 1):
                contagem = {s1: q1, s2: q2}
                largura, _ = largura_fileira(tipo, contagem)
                if largura > limite:
                    continue

                taxa1 = q1 * _nav(tipo, s1)["pares"]
                taxa2 = q2 * _nav(tipo, s2)["pares"]
                # A combinação roda até que o primeiro dos dois tamanhos complete.
                batidas_par = min(
                    teto_div(alvos[s1], taxa1),
                    teto_div(alvos[s2], taxa2),
                )
                etapa_par = criar_etapa(tipo, contagem, batidas_par)
                produz1 = batidas_par * taxa1
                produz2 = batidas_par * taxa2
                restante1 = max(0.0, alvos[s1] - produz1)
                restante2 = max(0.0, alvos[s2] - produz2)

                if restante1 <= 1e-9 and restante2 <= 1e-9:
                    blocos.append(finalizar_bloco(tipo, (s1, s2), [etapa_par]))
                elif restante1 > 1e-9:
                    # s2 terminou primeiro; s1 permanece e segue sozinho.
                    for q_solo in range(1, max_navalhas_largura(tipo, s1) + 1):
                        solo = {s1: q_solo}
                        if largura_simples(tipo, s1, q_solo) > limite:
                            continue
                        taxa_solo = q_solo * _nav(tipo, s1)["pares"]
                        n_solo = teto_div(restante1, taxa_solo)
                        etapa_solo = criar_etapa(tipo, solo, n_solo)
                        blocos.append(finalizar_bloco(tipo, (s1, s2), [etapa_par, etapa_solo]))
                else:
                    # s1 terminou primeiro; s2 permanece e segue sozinho.
                    for q_solo in range(1, max_navalhas_largura(tipo, s2) + 1):
                        solo = {s2: q_solo}
                        if largura_simples(tipo, s2, q_solo) > limite:
                            continue
                        taxa_solo = q_solo * _nav(tipo, s2)["pares"]
                        n_solo = teto_div(restante2, taxa_solo)
                        etapa_solo = criar_etapa(tipo, solo, n_solo)
                        blocos.append(finalizar_bloco(tipo, (s1, s2), [etapa_par, etapa_solo]))

    # Deduplica candidatos com a mesma estrutura e mesmo número de batidas.
    unicos = {}
    for b in blocos:
        chave = (
            b["tamanhos"],
            tuple((tuple(sorted(e["contagem"].items())), e["batidas"]) for e in b["etapas"]),
        )
        unicos[chave] = b
    return list(unicos.values())


# ---------------------------------------------------------------------------
# 6) OTIMIZAÇÃO GLOBAL (CP-SAT)
# ---------------------------------------------------------------------------


def _resolver_configurado():
    from ortools.sat.python import cp_model

    validar_dados()
    tamanhos = list(PARES_POR_TAMANHO)
    tons = list(TONS_METROS)
    blocos = {k: gerar_blocos(k, tamanhos) for k in COMPONENTES}
    for k in COMPONENTES:
        print(f"Campanhas candidatas de {k}: {len(blocos[k])}")

    cap = {t: round(TONS_METROS[t] * METRO) for t in tons}
    model = cp_model.CpModel()

    # Cada tamanho recebe exatamente uma tonalidade, compartilhada entre gaspeas.
    tom = {(s, t): model.new_bool_var(f"tom_{s}_{i}") for s in tamanhos for i, t in enumerate(tons)}
    for s in tamanhos:
        model.add_exactly_one(tom[s, t] for t in tons)

    # x[k,b,t] seleciona uma campanha completa para um componente e uma tonalidade.
    x = {}
    for k in COMPONENTES:
        for b_idx, bloco in enumerate(blocos[k]):
            for t_idx, t in enumerate(tons):
                var = model.new_bool_var(f"camp_{k}_{b_idx}_{t_idx}")
                x[k, b_idx, t] = var
                for s in bloco["tamanhos"]:
                    model.add(var <= tom[s, t])

    # Para cada tamanho e componente, exatamente um bloco é responsável por toda a produção.
    for k in COMPONENTES:
        for s in tamanhos:
            model.add(
                sum(
                    x[k, b_idx, t]
                    for b_idx, bloco in enumerate(blocos[k])
                    if s in bloco["tamanhos"]
                    for t in tons
                ) == 1
            )

    # O estoque de cada tonalidade é compartilhado por todos os componentes.
    for t in tons:
        model.add(
            sum(
                x[k, b_idx, t] * bloco["consumo_100"]
                for k in COMPONENTES
                for b_idx, bloco in enumerate(blocos[k])
            ) <= cap[t]
        )

    # Minimiza metragem total. A produção em cada bloco já é calculada em batidas inteiras.
    model.minimize(
        sum(
            x[k, b_idx, t] * bloco["consumo_100"]
            for k in COMPONENTES
            for b_idx, bloco in enumerate(blocos[k])
            for t in tons
        )
    )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = TEMPO_LIMITE_S
    solver.parameters.num_workers = 8
    status = solver.solve(model)
    print(f"Status: {solver.status_name(status)}")
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("Sem solução viável: revise estoque, demanda, largura ou dimensões das navalhas.")
        return None
    if status == cp_model.FEASIBLE:
        print("Atenção: solução viável, mas NÃO provada ótima (tempo esgotado).")

    atribuicao = {
        s: next(t for t in tons if solver.value(tom[s, t])) for s in tamanhos
    }
    selecionados = {t: {k: [] for k in COMPONENTES} for t in tons}
    for k in COMPONENTES:
        for b_idx, bloco in enumerate(blocos[k]):
            for t in tons:
                if solver.value(x[k, b_idx, t]):
                    selecionados[t][k].append(bloco)

    return montar_resultado(selecionados, atribuicao, tons, cap)


def resolver(configuracao: dict):
    """Executa o otimizador usando exclusivamente os dados recebidos.

    Formato esperado: demanda, navalhas, estoque_tons_metros, largura_mesa_cm,
    margem_seguranca_cm, perda_trocas_percentual, folga_entre_navalhas_cm,
    acrescimo_comprimento_cm e, opcionalmente, max_tamanhos_por_fileira e
    tempo_limite_segundos.
    """
    global TIPOS, NAVALHAS, PARES_POR_TAMANHO, COMPONENTES, TONS_METROS
    global LARGURA_MESA, MARGEM_SEGURANCA, FOLGA_ENTRE_NAVALHAS
    global PERC_TROCAS, MAX_TAMANHOS_POR_FILEIRA, TEMPO_LIMITE_S

    if not isinstance(configuracao, dict):
        raise TypeError("A configuração deve ser um dicionário.")
    obrigatorios = {
        "demanda", "navalhas", "estoque_tons_metros", "largura_mesa_cm",
        "margem_seguranca_cm", "perda_trocas_percentual",
        "folga_entre_navalhas_cm", "acrescimo_comprimento_cm",
    }
    faltantes = sorted(obrigatorios - configuracao.keys())
    if faltantes:
        raise ValueError("Dados ausentes na configuração: " + ", ".join(faltantes))

    PARES_POR_TAMANHO = {str(k): int(v) for k, v in configuracao["demanda"].items()}
    TONS_METROS = {str(k): float(v) for k, v in configuracao["estoque_tons_metros"].items()}
    if not PARES_POR_TAMANHO or not TONS_METROS:
        raise ValueError("Informe demanda e pelo menos uma tonalidade de estoque.")

    lista_navalhas = configuracao["navalhas"]
    if not isinstance(lista_navalhas, list):
        raise ValueError("'navalhas' deve ser uma lista de registros.")
    NAVALHAS = {}
    COMPONENTES = sorted({str(n["componente"]).strip() for n in lista_navalhas})
    acrescimos = configuracao["acrescimo_comprimento_cm"]
    TIPOS = {
        c: {
            "encaixe": False,
            "acrescimo_comprimento": cm(float(acrescimos.get(c, ACRESCIMO_COMPRIMENTO / ESCALA))),
        }
        for c in COMPONENTES
    }
    for n in lista_navalhas:
        componente = str(n["componente"]).strip()
        tamanho = str(n["tamanho"]).strip()
        chave = (componente, tamanho)
        if chave in NAVALHAS:
            raise ValueError(f"Navalha duplicada: {componente}/{tamanho}.")
        NAVALHAS[chave] = navalha(
            float(n["largura_cm"]), float(n["comprimento_cm"]),
            float(n.get("pares_por_batida", 1)),
            largura2=n.get("largura2_cm"),
            comprimento2=n.get("comprimento2_cm"),
        )
        if n.get("encaixe"):
            TIPOS[componente]["encaixe"] = True

    LARGURA_MESA = cm(float(configuracao["largura_mesa_cm"]))
    MARGEM_SEGURANCA = cm(float(configuracao["margem_seguranca_cm"]))
    FOLGA_ENTRE_NAVALHAS = cm(float(configuracao["folga_entre_navalhas_cm"]))
    PERC_TROCAS = int(float(configuracao["perda_trocas_percentual"]))
    if float(configuracao["perda_trocas_percentual"]) != PERC_TROCAS:
        raise ValueError("A perda por trocas deve ser um percentual inteiro.")
    MAX_TAMANHOS_POR_FILEIRA = int(configuracao.get("max_tamanhos_por_fileira", 2))
    TEMPO_LIMITE_S = float(configuracao.get("tempo_limite_segundos", 60))

    validar_dados()
    return _resolver_configurado()


# ---------------------------------------------------------------------------
# 7) RESULTADO + VALIDAÇÃO INDEPENDENTE
# ---------------------------------------------------------------------------


def montar_resultado(selecionados, atribuicao, tons, cap) -> dict:
    resultado = {"metros_totais": 0.0, "tons": {}}
    fator_rendimento = (100 - PERC_TROCAS) / 100

    for t in tons:
        tamanhos_t = [s for s, tt in atribuicao.items() if tt == t]
        campanhas = []
        usado100 = 0
        producao_bruta = {k: {s: 0.0 for s in tamanhos_t} for k in COMPONENTES}

        for k in COMPONENTES:
            for bloco in selecionados[t][k]:
                # As etapas de uma campanha são impressas em ordem: combinação e,
                # se necessário, continuação solo do tamanho que ainda não terminou.
                etapas_saida = []
                for etapa in bloco["etapas"]:
                    usado100 += etapa["consumo_100"]
                    for s, pares in etapa["pares_brutos"].items():
                        producao_bruta[k][s] += pares
                    etapas_saida.append({
                        "sequencia": etapa["descricao"],
                        "batidas": etapa["batidas"],
                        "contagem": dict(etapa["contagem"]),
                        "largura_cm": etapa["largura_100"] / ESCALA,
                        "posicao_esquerda": etapa["esquerda"],
                        "comprimento_batida_cm": etapa["comprimento_100"] / ESCALA,
                        "metros": etapa["consumo_100"] / METRO,
                        "pares_brutos": etapa["pares_brutos"],
                    })
                campanhas.append({
                    "componente": k,
                    "tamanhos": list(bloco["tamanhos"]),
                    "etapas": etapas_saida,
                    "metros": bloco["consumo_100"] / METRO,
                    "producao_bruta": bloco["producao_bruta"],
                })

        assert usado100 <= cap[t], f"Metragem estourada em {t}"
        producao_efetiva = {
            k: {s: v * fator_rendimento for s, v in d.items()}
            for k, d in producao_bruta.items()
        }
        for k in COMPONENTES:
            for s in tamanhos_t:
                assert producao_efetiva[k][s] + 1e-9 >= PARES_POR_TAMANHO[s], (
                    f"Demanda não atendida: {k} {s} em {t}"
                )

        resultado["tons"][t] = {
            "tamanhos": tamanhos_t,
            "campanhas": campanhas,
            "producao_pares_brutos": {
                k: {s: round(v, 2) for s, v in d.items()} for k, d in producao_bruta.items()
            },
            "producao_pares_efetivos": {
                k: {s: round(v, 2) for s, v in d.items()} for k, d in producao_efetiva.items()
            },
            "metros_usados": usado100 / METRO,
            "metros_disponiveis": cap[t] / METRO,
        }
        resultado["metros_totais"] += usado100 / METRO
    return resultado


def imprimir(resultado: dict) -> None:
    print(f"\nMetros totais: {resultado['metros_totais']:.2f} m\n")
    for t, d in resultado["tons"].items():
        print(f"== {t}: tamanhos {', '.join(d['tamanhos']) or '(nenhum)'} ==")
        for campanha in d["campanhas"]:
            print(f"  [{campanha['componente']}] campanha dos tamanhos {', '.join(campanha['tamanhos'])}")
            for i, etapa in enumerate(campanha["etapas"], start=1):
                pares = ", ".join(f"{s}: {v}" for s, v in etapa["pares_brutos"].items())
                print(
                    f"      Etapa {i}: {etapa['sequencia']} -> {etapa['batidas']} batidas "
                    f"x {etapa['comprimento_batida_cm']:.2f} cm = {etapa['metros']:.2f} m"
                )
                print(f"          pares brutos produzidos: {pares}")
        print(f"  Produção bruta (pares): {d['producao_pares_brutos']}")
        print(f"  Produção efetiva após {PERC_TROCAS}% de perda: {d['producao_pares_efetivos']}")
        print(f"  Tecido: {d['metros_usados']:.2f} m de {d['metros_disponiveis']:.2f} m\n")


# ---------------------------------------------------------------------------
# 8) AUTOTESTE: fórmulas da planilha
# ---------------------------------------------------------------------------


def autoteste() -> None:
    bat = batidas_largura_encaixe(cm(22.8), cm(21.3), cm(130.3))
    fpm = fileiras_por_metro_encaixe_100(cm(23.6), cm(18.9))
    assert (bat, fpm) == (6, 504), (bat, fpm)
    assert consumo_100(bat, 1, fpm, 1) // 100 == 29
    bat_comp = batidas_largura_encaixe(cm(25.9), cm(23.7), cm(145.4))
    fpm2 = fileiras_por_metro_encaixe_100(cm(17.7), cm(17.7))
    assert (bat_comp, fpm2) == (6, 564), (bat_comp, fpm2)
    assert consumo_100(bat_comp, 4, fpm2, 1) == 13400
    bat_q = cm(67.8) // cm(17.4)
    fpm_q = fileiras_por_metro_simples_100(cm(18.5), cm(0.3))
    assert (bat_q, fpm_q) == (3, 531), (bat_q, fpm_q)
    assert consumo_100(bat_q, 3, fpm_q, 1) == 4731
    assert componentes_por_batida(0.5) == 1 and componentes_por_batida(1) == 2
    assert consumo_100(6, 0.5, 504, 1) == 1496 and consumo_100(6, 1, 504, 1) == 2993
    try:
        componentes_por_batida(0.3)
        raise AssertionError("0,3 deveria ser recusado")
    except ValueError:
        pass
    assert cm(138.0) <= LARGURA_MESA - MARGEM_SEGURANCA < cm(139.0)
    print("Autoteste OK: fórmulas da planilha e regra de largura validadas.")


if __name__ == "__main__":
    if "--teste" in sys.argv:
        autoteste()
    else:
        print("Este módulo contém o algoritmo e aguarda dados via resolver(configuracao).")
        print("Execute a interface: python tonalidades_tkinter.py")
