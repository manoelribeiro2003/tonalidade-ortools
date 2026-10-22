"""
Divisão de tonalidades v2 (Google OR-Tools, CP-SAT)

O que o modelo faz
------------------
1. Gera as FILEIRAS possíveis de cada tipo de componente (cabedal, lingueta...),
   respeitando: largura útil = mesa - 1 cm, encaixe (largura 1 na primeira
   navalha, largura 2 nas demais), um bloco contíguo por tamanho e só um tipo
   de componente por fileira.
2. Calcula o CONSUMO (pares por metro) de cada tamanho em cada fileira, com as
   fórmulas da planilha de consumo.
3. O CP-SAT decide, ao mesmo tempo:
   - em que TOM cada tamanho será cortado (o tamanho inteiro vai para um único
     tom, e vale para todos os componentes: cabedal 334 e lingueta 334 no mesmo tom);
   - quantos metros de cada fileira cortar em cada tom,
   minimizando os METROS TOTAIS, sem passar da metragem de cada tom.

Suposições provisórias (marcadas com [SUPOSIÇÃO])
-------------------------------------------------
- Fileira com mais de um tamanho: cada tamanho rende suas batidas x pares por
  navalha x fileiras por metro x (1 - % trocas), sem batidas fracionadas.
  Se a regra da planilha for outra, troque APENAS a função consumo_100().
- A demanda é "pelo menos" (produção >= pares pedidos), porque o consumo é uma
  média em pares/m. O excedente é reportado no resultado.
- Rotação de 90 graus e divisão de um tamanho entre tons ficam de fora por enquanto.

Os dados abaixo são EXEMPLOS: substitua pelos reais.

Instalação:  pip install ortools
Execução:    python divisao_tonalidades_v2.py
Autoteste:   python divisao_tonalidades_v2.py --teste   (confere as fórmulas com a planilha)
"""

import json
import sys
from itertools import combinations, product

# ---------------------------------------------------------------------------
# 1) PARÂMETROS GERAIS
# ---------------------------------------------------------------------------

ESCALA = 100                      # cm -> centésimos de cm (tudo em inteiros)
METRO = 100 * ESCALA              # 1 metro em centésimos de cm


def cm(valor: float) -> int:
    return round(valor * ESCALA)


LARGURA_MESA = cm(139.0)
MARGEM_SEGURANCA = cm(1.0)        # regra prioritária: fileira de 139 é inválida, até 138 vale
FOLGA_ENTRE_NAVALHAS = cm(0.0)    # não é regra absoluta; 0 por padrão
ACRESCIMO_COMPRIMENTO = cm(0.4)   # planilha: 0,4 cm (0,3 cm na navalha quadrada)
PERC_TROCAS = 1                   # % de perda por trocas (planilha: 1%; versões antigas 2%; meia 5%)
MAX_TAMANHOS_POR_FILEIRA = 2      # por enquanto combinamos até dois tamanhos
TEMPO_LIMITE_S = 60

# ---------------------------------------------------------------------------
# 2) DADOS DE EXEMPLO (substitua pelos reais)
# ---------------------------------------------------------------------------

# O encaixe é propriedade do TIPO: vale para todos os tamanhos daquele tipo.
TIPOS = {
    "cabedal":  {"encaixe": True},
    "lingueta": {"encaixe": False, "acrescimo_comprimento": cm(0.3)},
}


def navalha(largura1, comprimento1, pares=1, largura2=None, comprimento2=None):
    """largura2: só para tipos de encaixe (largura quando encaixada à esquerda).
    comprimento2: só se houver encaixe também no comprimento (como na planilha)."""
    return {
        "largura1": cm(largura1),
        "largura2": cm(largura2) if largura2 is not None else cm(largura1),
        "comprimento1": cm(comprimento1),
        "comprimento2": cm(comprimento2) if comprimento2 is not None else None,
        "pares": pares,
    }


# chave = (tipo, tamanho)
NAVALHAS = {
    # cabedal (encaixe)
    ("cabedal", "334"): navalha(17.42, 13.23, 1, largura2=16.62),
    ("cabedal", "35"):  navalha(17.70, 13.50, 1, largura2=16.80),
    ("cabedal", "394"): navalha(19.00, 14.94, 1, largura2=18.12),
    # lingueta (sem encaixe, largura única)
    ("lingueta", "334"): navalha(17.4, 18.5, 3),
    ("lingueta", "35"):  navalha(17.8, 18.9, 3),
    ("lingueta", "394"): navalha(19.5, 20.3, 3),
}

# Ordem de produção: pares por tamanho e componentes do calçado
PARES_POR_TAMANHO = {"334": 20, "35": 40, "394": 60}
COMPONENTES = ["cabedal", "lingueta"]

# Reserva do almoxarifado por tom (em metros)
TONS_METROS = {"tom 1": 2.0, "tom 2": 1.5, "tom 3": 0.6}


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


def consumo_100(batidas: int, pares: int, fileiras_metro_100: int, perc_trocas: int) -> int:
    """Consumo em CENTÉSIMOS de pares/m: batidas x pares/nav x fileiras/m x (100-% trocas)/100.
    [SUPOSIÇÃO para fileiras com mais de um tamanho: ver cabeçalho.]"""
    return batidas * pares * fileiras_metro_100 * (100 - perc_trocas) // 100


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
            contagem, key=lambda t: _nav(tipo, t)["largura1"] - _nav(tipo, t)["largura2"]
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


def gerar_fileiras(tipo: str, tamanhos: list) -> list:
    limite = LARGURA_MESA - MARGEM_SEGURANCA
    encaixe = TIPOS[tipo]["encaixe"]
    menor = min(
        (_nav(tipo, t)["largura2"] if encaixe else _nav(tipo, t)["largura1"]) for t in tamanhos
    )
    max_bat = limite // menor + 1

    fileiras = []
    for k in range(1, MAX_TAMANHOS_POR_FILEIRA + 1):
        for combo in combinations(tamanhos, k):
            for contagens in product(range(1, max_bat + 1), repeat=k):
                contagem = dict(zip(combo, contagens))
                largura, primeiro = largura_fileira(tipo, contagem)
                if largura > limite:
                    continue
                fpm = fileiras_por_metro_100(tipo, combo)
                fileiras.append(
                    {
                        "tipo": tipo,
                        "contagem": contagem,
                        "esquerda": primeiro,
                        "largura": largura,
                        "fileiras_metro_100": fpm,
                        "consumo100": {
                            t: consumo_100(n, _nav(tipo, t)["pares"], fpm, PERC_TROCAS)
                            for t, n in contagem.items()
                        },
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
                assert n["largura2"] <= n["largura1"], f"Largura 2 deve ser <= largura 1 ({tipo} {tam})"


# ---------------------------------------------------------------------------
# 5) OTIMIZAÇÃO (CP-SAT)
# ---------------------------------------------------------------------------

def resolver():
    from ortools.sat.python import cp_model  # import tardio: o resto roda sem ortools

    validar_dados()
    tamanhos = list(PARES_POR_TAMANHO)
    fileiras = {k: gerar_fileiras(k, tamanhos) for k in COMPONENTES}
    for k in COMPONENTES:
        print(f"Fileiras viáveis de {k}: {len(fileiras[k])}")

    tons = list(TONS_METROS)
    cap = {t: round(TONS_METROS[t] * 100) for t in tons}  # centímetros de tecido

    model = cp_model.CpModel()

    # tom[s, t] = 1 se o tamanho s é cortado (inteiro) no tom t
    tom = {(s, t): model.new_bool_var(f"tom_{s}_{t}") for s in tamanhos for t in tons}
    for s in tamanhos:
        model.add_exactly_one(tom[s, t] for t in tons)

    # m[k, j, t] = centímetros cortados da fileira j do componente k no tom t
    m = {}
    for k in COMPONENTES:
        for j, f in enumerate(fileiras[k]):
            for t in tons:
                v = model.new_int_var(0, cap[t], f"m_{k}_{j}_{t}")
                m[k, j, t] = v
                # a fileira só pode rodar no tom t se TODOS os seus tamanhos estiverem nesse tom
                for s in f["contagem"]:
                    model.add(v <= cap[t] * tom[s, t])

    for t in tons:
        # metragem do tom (componentes diferentes cortam trechos diferentes: os metros se somam)
        model.add(sum(m[k, j, t] for k in COMPONENTES for j in range(len(fileiras[k]))) <= cap[t])

        # demanda: pares(x10000) = consumo100 (centi-pares/m) x centímetros
        for k in COMPONENTES:
            for s in tamanhos:
                producao = sum(
                    f["consumo100"][s] * m[k, j, t]
                    for j, f in enumerate(fileiras[k])
                    if s in f["contagem"]
                )
                model.add(producao >= PARES_POR_TAMANHO[s] * 10000 * tom[s, t])

    model.minimize(sum(m.values()))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = TEMPO_LIMITE_S
    solver.parameters.num_workers = 8
    status = solver.solve(model)
    print(f"Status: {solver.status_name(status)}")
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("Sem solução viável: revise a metragem dos tons, a demanda ou as navalhas.")
        return None
    if status == cp_model.FEASIBLE:
        print("Atenção: solução viável, mas NÃO provada ótima (tempo esgotado).")

    valores = {chave: solver.value(var) for chave, var in m.items()}
    atribuicao = {s: next(t for t in tons if solver.value(tom[s, t])) for s in tamanhos}
    return montar_resultado(fileiras, valores, atribuicao, tons, cap)


# ---------------------------------------------------------------------------
# 6) RESULTADO + VALIDAÇÃO INDEPENDENTE
# ---------------------------------------------------------------------------

def montar_resultado(fileiras, valores, atribuicao, tons, cap) -> dict:
    resultado = {"metros_totais": 0.0, "tons": {}}
    for t in tons:
        tamanhos_t = [s for s, tt in atribuicao.items() if tt == t]
        cortes = []
        usado_cm = 0
        producao = {k: {s: 0.0 for s in tamanhos_t} for k in COMPONENTES}

        for k in COMPONENTES:
            for j, f in enumerate(fileiras[k]):
                cm_cortados = valores[k, j, t]
                if cm_cortados == 0:
                    continue
                usado_cm += cm_cortados
                cortes.append(
                    {
                        "componente": k,
                        "fileira": descrever(f),
                        "esquerda": f["esquerda"],
                        "metros": cm_cortados / 100,
                        "fileiras_aprox": round(cm_cortados / 100 * f["fileiras_metro_100"] / 100, 1),
                        "consumo_pares_m": {s: v / 100 for s, v in f["consumo100"].items()},
                    }
                )
                for s, c100 in f["consumo100"].items():
                    assert s in tamanhos_t, "fileira com tamanho de outro tom"
                    producao[k][s] += c100 * cm_cortados / 10000

        # validação independente do solver
        assert usado_cm <= cap[t], f"Metragem estourada em {t}"
        for k in COMPONENTES:
            for s in tamanhos_t:
                assert producao[k][s] + 1e-9 >= PARES_POR_TAMANHO[s], f"Demanda não atendida: {k} {s} em {t}"

        resultado["tons"][t] = {
            "tamanhos": tamanhos_t,
            "cortes": cortes,
            "producao_pares": {k: {s: round(v, 2) for s, v in d.items()} for k, d in producao.items()},
            "metros_usados": usado_cm / 100,
            "metros_disponiveis": cap[t] / 100,
        }
        resultado["metros_totais"] += usado_cm / 100
    return resultado


def imprimir(resultado: dict) -> None:
    print(f"\nMetros totais: {resultado['metros_totais']:.2f} m\n")
    for t, d in resultado["tons"].items():
        print(f"== {t}: tamanhos {', '.join(d['tamanhos']) or '(nenhum)'} ==")
        for c in d["cortes"]:
            cons = ", ".join(f"{s}: {v:.2f}" for s, v in c["consumo_pares_m"].items())
            print(f"  [{c['componente']}] {c['fileira']}  -> {c['metros']:.2f} m (~{c['fileiras_aprox']} fileiras)")
            print(f"      consumo (pares/m): {cons}")
        print(f"  Produção (pares): {d['producao_pares']}")
        print(f"  Tecido: {d['metros_usados']:.2f} m de {d['metros_disponiveis']:.2f} m\n")


# ---------------------------------------------------------------------------
# 7) AUTOTESTE: reproduz resultados que estão na planilha
# ---------------------------------------------------------------------------

def autoteste() -> None:
    # aba "calculo nav.encaixe", bloco 1: resultado 29 pares/m
    bat = batidas_largura_encaixe(cm(22.8), cm(21.3), cm(130.3))
    fpm = fileiras_por_metro_encaixe_100(cm(23.6), cm(18.9))
    assert (bat, fpm) == (6, 504), (bat, fpm)
    c = consumo_100(bat, 1, fpm, 1)
    assert c // 100 == 29, c

    # aba "calculo nav.encaixe", bloco 2 (girada): resultado 134
    bat_comp = batidas_largura_encaixe(cm(25.9), cm(23.7), cm(145.4))
    fpm2 = fileiras_por_metro_encaixe_100(cm(17.7), cm(17.7))
    assert (bat_comp, fpm2) == (6, 564), (bat_comp, fpm2)
    assert consumo_100(bat_comp, 4, fpm2, 1) == 13400

    # aba "calculo nav quadrada": resultado 47,31
    bat_q = cm(67.8) // cm(17.4)
    fpm_q = fileiras_por_metro_simples_100(cm(18.5), cm(0.3))
    assert (bat_q, fpm_q) == (3, 531), (bat_q, fpm_q)
    assert consumo_100(bat_q, 3, fpm_q, 1) == 4731

    # regra da folga: 138 é válido, 139 não (mesa de 139 cm)
    assert cm(138.0) <= LARGURA_MESA - MARGEM_SEGURANCA < cm(139.0)
    print("Autoteste OK: fórmulas batem com a planilha (29, 134 e 47,31).")


if __name__ == "__main__":
    if "--teste" in sys.argv:
        autoteste()
        sys.exit(0)

    res = resolver()
    if res:
        imprimir(res)
        with open("resultado_divisao_v2.json", "w", encoding="utf-8") as fh:
            json.dump(res, fh, ensure_ascii=False, indent=2)
        print("Resultado salvo em resultado_divisao_v2.json")
