"""
Divisão de tonalidades com Google OR-Tools (CP-SAT)

Ideia do modelo (duas camadas, como no seu texto):

1. GEOMETRIA  -> gerar todas as batidas (combinações de navalhas) que cabem
                 na largura útil de 143 cm. Isso é enumeração, não otimização.
2. OTIMIZAÇÃO -> o CP-SAT decide, ao mesmo tempo:
                 a) em qual tonalidade (rolo) cada conjunto/pedido será cortado;
                 b) quantas vezes cada batida é executada em cada tonalidade,
                 de modo a atender a demanda EXATA e minimizar o comprimento
                 total de tecido consumido.

Instalação:  pip install ortools
Execução:    python divisao_tonalidades.py
"""


from itertools import combinations, combinations_with_replacement

from ortools.sat.python import cp_model

# ---------------------------------------------------------------------------
# 1) DADOS DE ENTRADA  (edite aqui)
# ---------------------------------------------------------------------------

# CP-SAT só trabalha com inteiros: trabalhamos em centésimos de cm.
ESCALA = 100


def cm(valor: float) -> int:
    return round(valor * ESCALA)


LARGURA_UTIL = cm(143.0)
ESPACAMENTO = cm(0.5)

# Largura = soma dos dois valores registrados; comprimento = o outro valor.
NAVALHAS = {
    334: {"largura": cm(17.42) + cm(16.62), "comprimento": cm(13.23)},
    356: {"largura": cm(17.73) + cm(16.90), "comprimento": cm(13.58)},
    378: {"largura": cm(18.33) + cm(17.44), "comprimento": cm(14.28)},
    394: {"largura": cm(19.00) + cm(18.12), "comprimento": cm(14.94)},
}

# Pares de navalhas que NÃO podem dividir a mesma batida (regra de compatibilidade).
# Exemplo: {frozenset({334, 394})}
INCOMPATIVEIS: set[frozenset] = set()

# Comprimento disponível (cm) em cada tonalidade (soma dos rolos daquela tonalidade).
TONALIDADES = {
    "T1": cm(900),
    "T2": cm(700),
    "T3": cm(550),
}

# Demanda por conjunto/pedido: {navalha: quantidade}.
# Regra assumida: todas as peças de um conjunto saem de UMA única tonalidade.
CONJUNTOS = {
    "pedido_A": {334: 120, 356: 80},
    "pedido_B": {378: 60, 394: 40},
    "pedido_C": {334: 50, 378: 70},
}

TEMPO_LIMITE_S = 30


# ---------------------------------------------------------------------------
# 2) GEOMETRIA: gerar as batidas viáveis
# ---------------------------------------------------------------------------

def largura_ocupada(combo: tuple) -> int:
    """Soma das larguras + espaçamento entre as navalhas.
    Ajuste aqui se o seu algoritmo contar folga nas extremidades."""
    larguras = sum(NAVALHAS[n]["largura"] for n in combo)
    return larguras + ESPACAMENTO * (len(combo) - 1)


def avanco(combo: tuple) -> int:
    """Avanço vertical = maior comprimento da batida + espaçamento."""
    return max(NAVALHAS[n]["comprimento"] for n in combo) + ESPACAMENTO


def tem_par_incompativel(combo: tuple) -> bool:
    return any(frozenset(par) in INCOMPATIVEIS for par in combinations(set(combo), 2))


def gerar_batidas() -> list[dict]:
    ids = sorted(NAVALHAS)
    menor = min(NAVALHAS[n]["largura"] for n in ids)
    max_pecas = (LARGURA_UTIL + ESPACAMENTO) // (menor + ESPACAMENTO)

    batidas = []
    for k in range(1, max_pecas + 1):
        for combo in combinations_with_replacement(ids, k):
            if largura_ocupada(combo) > LARGURA_UTIL:
                continue
            if tem_par_incompativel(combo):
                continue
            batidas.append(
                {
                    "combo": combo,
                    "qtd": {n: combo.count(n) for n in ids},
                    "avanco": avanco(combo),
                }
            )
    return batidas


# ---------------------------------------------------------------------------
# 3) OTIMIZAÇÃO: modelo CP-SAT
# ---------------------------------------------------------------------------

def resolver():
    batidas = gerar_batidas()
    print(f"Batidas viáveis geradas: {len(batidas)}")

    navalhas_ids = sorted(NAVALHAS)
    total_unidades = sum(q for dem in CONJUNTOS.values() for q in dem.values())

    model = cp_model.CpModel()

    # atrib[c, t] = 1 se o conjunto c é cortado na tonalidade t
    atrib = {
        (c, t): model.new_bool_var(f"atrib_{c}_{t}")
        for c in CONJUNTOS
        for t in TONALIDADES
    }
    for c in CONJUNTOS:
        model.add_exactly_one(atrib[c, t] for t in TONALIDADES)

    # x[j, t] = número de execuções da batida j na tonalidade t
    x = {
        (j, t): model.new_int_var(0, total_unidades, f"x_{j}_{t}")
        for j in range(len(batidas))
        for t in TONALIDADES
    }

    for t in TONALIDADES:
        # Demanda exata: produção de cada navalha na tonalidade t
        # == soma da demanda dos conjuntos atribuídos a t
        for n in navalhas_ids:
            producao = sum(b["qtd"][n] * x[j, t] for j, b in enumerate(batidas))
            demanda = sum(CONJUNTOS[c].get(n, 0) * atrib[c, t] for c in CONJUNTOS)
            model.add(producao == demanda)

        # Capacidade: comprimento consumido não pode passar do que há na tonalidade
        consumo_t = sum(b["avanco"] * x[j, t] for j, b in enumerate(batidas))
        model.add(consumo_t <= TONALIDADES[t])

    # Objetivo: minimizar o comprimento total de tecido consumido
    consumo_total = sum(
        b["avanco"] * x[j, t] for j, b in enumerate(batidas) for t in TONALIDADES
    )
    model.minimize(consumo_total)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = TEMPO_LIMITE_S
    solver.parameters.num_workers = 8
    status = solver.solve(model)

    print(f"Status: {solver.status_name(status)}")
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("Sem solução viável: revise demanda, comprimentos ou compatibilidades.")
        return None

    if status == cp_model.FEASIBLE:
        print("Atenção: solução viável, mas NÃO provada ótima (tempo esgotado).")

    # -----------------------------------------------------------------------
    # 4) RESULTADO + VALIDAÇÃO INDEPENDENTE
    # -----------------------------------------------------------------------
    resultado = {"consumo_total_cm": solver.objective_value / ESCALA, "tonalidades": {}}

    for t in TONALIDADES:
        conjuntos_t = [c for c in CONJUNTOS if solver.value(atrib[c, t])]
        batidas_t = []
        producao = {n: 0 for n in navalhas_ids}
        comprimento = 0

        for j, b in enumerate(batidas):
            vezes = solver.value(x[j, t])
            if vezes == 0:
                continue
            batidas_t.append({"navalhas": list(b["combo"]), "execucoes": vezes})
            comprimento += b["avanco"] * vezes
            for n in navalhas_ids:
                producao[n] += b["qtd"][n] * vezes

        demanda = {n: sum(CONJUNTOS[c].get(n, 0) for c in conjuntos_t) for n in navalhas_ids}
        assert producao == demanda, f"Quantidades divergentes em {t}"
        assert comprimento <= TONALIDADES[t], f"Tecido insuficiente em {t}"

        resultado["tonalidades"][t] = {
            "conjuntos": conjuntos_t,
            "batidas": batidas_t,
            "producao": producao,
            "comprimento_usado_cm": comprimento / ESCALA,
            "comprimento_disponivel_cm": TONALIDADES[t] / ESCALA,
        }

    return resultado


def imprimir(resultado: dict) -> None:
    print(f"\nConsumo total: {resultado['consumo_total_cm']:.2f} cm\n")
    for t, dados in resultado["tonalidades"].items():
        print(f"== Tonalidade {t} ==")
        print(f"  Conjuntos: {', '.join(dados['conjuntos']) or '(nenhum)'}")
        for b in dados["batidas"]:
            print(f"  Batida {b['navalhas']} x {b['execucoes']}")
        print(f"  Produção: {dados['producao']}")
        print(
            f"  Tecido: {dados['comprimento_usado_cm']:.2f} cm "
            f"de {dados['comprimento_disponivel_cm']:.2f} cm\n"
        )
