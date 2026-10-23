# Scripts

O seguinte documento tem como finalidade explicar o qeu cada script tenta alcançar.

## ChatGPT
Dentro de [divisao_tonalidades_batidas_inteiras.py](./src/testecloud/chatgpt/divisao_tonalidades_batidas_inteiras.py) é tentado "prever" ou planejas as batidas de modo que tenha um plano de batidas e que assim faça com que a produção seja atendida:

```
Fileiras viáveis de gaspea_interna: 416
Fileiras viáveis de gaspea_externa: 438
Status: FEASIBLE
Atenção: solução viável, mas NÃO provada ótima (tempo esgotado).

Metros totais: 47.68 m

== tom 1: tamanhos 334, 36, 39, 41, 42, 45 ==
  [gaspea_interna] 5x36  (larg. 125.75 cm) -> 1 batidas x 17.23 cm = 0.17 m
      pares brutos produzidos: 36: 5
  [gaspea_interna] 5x39  (larg. 136.00 cm) -> 1 batidas x 18.39 cm = 0.18 m
      pares brutos produzidos: 39: 5
  [gaspea_interna] 4x45  (larg. 121.60 cm) -> 10 batidas x 20.08 cm = 2.01 m
      pares brutos produzidos: 45: 40
  [gaspea_interna] 2x334 + 3x42  (larg. 136.34 cm) -> 22 batidas x 19.65 cm = 4.32 m
      pares brutos produzidos: 334: 44, 42: 66
  [gaspea_interna] 1x36 + 4x39  (larg. 133.95 cm) -> 2 batidas x 18.39 cm = 0.37 m
      pares brutos produzidos: 36: 2, 39: 8
  [gaspea_interna] 3x36 + 2x39  (larg. 129.85 cm) -> 1 batidas x 18.39 cm = 0.18 m
      pares brutos produzidos: 36: 3, 39: 2
  [gaspea_interna] 1x36 + 4x41  (larg. 136.67 cm) -> 17 batidas x 18.69 cm = 3.18 m
      pares brutos produzidos: 36: 17, 41: 68
  [gaspea_interna] 2x36 + 3x41  (larg. 133.94 cm) -> 2 batidas x 18.69 cm = 0.37 m
      pares brutos produzidos: 36: 4, 41: 6
  [gaspea_interna] 3x36 + 2x42  (larg. 134.01 cm) -> 10 batidas x 19.65 cm = 1.97 m
      pares brutos produzidos: 36: 30, 42: 20
  [gaspea_interna] 3x39 + 2x41  (larg. 137.36 cm) -> 16 batidas x 18.69 cm = 2.99 m
      pares brutos produzidos: 39: 48, 41: 32
  [gaspea_interna] 4x39 + 1x41  (larg. 136.68 cm) -> 1 batidas x 18.69 cm = 0.19 m
      pares brutos produzidos: 39: 4, 41: 1
  [gaspea_interna] 1x39 + 3x42  (larg. 115.04 cm) -> 3 batidas x 19.65 cm = 0.59 m
      pares brutos produzidos: 39: 3, 42: 9
  [gaspea_interna] 1x42 + 3x45  (larg. 120.48 cm) -> 1 batidas x 20.08 cm = 0.20 m
      pares brutos produzidos: 42: 1, 45: 3
  [gaspea_interna] 2x42 + 2x45  (larg. 119.36 cm) -> 1 batidas x 20.08 cm = 0.20 m
      pares brutos produzidos: 42: 2, 45: 2
  [gaspea_externa] 5x334  (larg. 118.70 cm) -> 2 batidas x 14.47 cm = 0.29 m
      pares brutos produzidos: 334: 10
  [gaspea_externa] 5x39  (larg. 133.25 cm) -> 12 batidas x 15.81 cm = 1.90 m
      pares brutos produzidos: 39: 60
  [gaspea_externa] 5x41  (larg. 137.40 cm) -> 21 batidas x 16.15 cm = 3.39 m
      pares brutos produzidos: 41: 105
  [gaspea_externa] 2x334 + 3x42  (larg. 133.61 cm) -> 2 batidas x 16.76 cm = 0.34 m
      pares brutos produzidos: 334: 4, 42: 6
  [gaspea_externa] 2x334 + 3x45  (larg. 137.06 cm) -> 15 batidas x 17.27 cm = 2.59 m
      pares brutos produzidos: 334: 30, 45: 45
  [gaspea_externa] 1x36 + 4x39  (larg. 131.34 cm) -> 1 batidas x 15.81 cm = 0.16 m
      pares brutos produzidos: 36: 1, 39: 4
  [gaspea_externa] 2x36 + 3x42  (larg. 135.61 cm) -> 30 batidas x 16.76 cm = 5.03 m
      pares brutos produzidos: 36: 60, 42: 90
  [gaspea_externa] 3x39 + 2x41  (larg. 134.91 cm) -> 1 batidas x 16.15 cm = 0.16 m
      pares brutos produzidos: 39: 3, 41: 2
  [gaspea_externa] 3x39 + 2x42  (larg. 137.37 cm) -> 1 batidas x 16.76 cm = 0.17 m
      pares brutos produzidos: 39: 3, 42: 2
  Produção bruta (pares): {'gaspea_interna': {'334': 44.0, '36': 61.0, '39': 70.0, '41': 107.0, '42': 98.0, '45': 45.0}, 'gaspea_externa': {'334': 44.0, '36': 61.0, '39': 70.0, '41': 107.0, '42': 98.0, '45': 45.0}}
  Produção efetiva após 1% de perda: {'gaspea_interna': {'334': 43.56, '36': 60.39, '39': 69.3, '41': 105.93, '42': 97.02, '45': 44.55}, 'gaspea_externa': {'334': 43.56, '36': 60.39, '39': 69.3, '41': 105.93, '42': 97.02, '45': 44.55}}
  Tecido: 30.94 m de 40.80 m

== tom 2: tamanhos 378, 40 ==
  [gaspea_interna] 5x378  (larg. 133.15 cm) -> 12 batidas x 18.19 cm = 2.18 m
      pares brutos produzidos: 378: 60
  [gaspea_interna] 5x40  (larg. 137.75 cm) -> 12 batidas x 18.54 cm = 2.22 m
      pares brutos produzidos: 40: 60
  [gaspea_interna] 1x378 + 4x40  (larg. 136.83 cm) -> 1 batidas x 18.54 cm = 0.19 m
      pares brutos produzidos: 378: 1, 40: 4
  [gaspea_externa] 5x378  (larg. 130.40 cm) -> 12 batidas x 15.58 cm = 1.87 m
      pares brutos produzidos: 378: 60
  [gaspea_externa] 5x40  (larg. 135.25 cm) -> 12 batidas x 16.00 cm = 1.92 m
      pares brutos produzidos: 40: 60
  [gaspea_externa] 1x378 + 4x40  (larg. 134.28 cm) -> 1 batidas x 16.00 cm = 0.16 m
      pares brutos produzidos: 378: 1, 40: 4
  Produção bruta (pares): {'gaspea_interna': {'378': 61.0, '40': 64.0}, 'gaspea_externa': {'378': 61.0, '40': 64.0}}
  Produção efetiva após 1% de perda: {'gaspea_interna': {'378': 60.39, '40': 63.36}, 'gaspea_externa': {'378': 60.39, '40': 63.36}}
  Tecido: 8.54 m de 24.70 m

== tom 3: tamanhos 35, 434 ==
  [gaspea_interna] 5x35  (larg. 124.05 cm) -> 1 batidas x 17.09 cm = 0.17 m
      pares brutos produzidos: 35: 5
  [gaspea_interna] 4x434  (larg. 119.48 cm) -> 5 batidas x 19.86 cm = 0.99 m
      pares brutos produzidos: 434: 20
  [gaspea_interna] 3x35 + 2x434  (larg. 134.17 cm) -> 17 batidas x 19.86 cm = 3.38 m
      pares brutos produzidos: 35: 51, 434: 34
  [gaspea_externa] 5x35  (larg. 121.65 cm) -> 4 batidas x 14.74 cm = 0.59 m
      pares brutos produzidos: 35: 20
  [gaspea_externa] 2x35 + 3x434  (larg. 136.44 cm) -> 18 batidas x 17.01 cm = 3.06 m
      pares brutos produzidos: 35: 36, 434: 54
  Produção bruta (pares): {'gaspea_interna': {'35': 56.0, '434': 54.0}, 'gaspea_externa': {'35': 56.0, '434': 54.0}}
  Produção efetiva após 1% de perda: {'gaspea_interna': {'35': 55.44, '434': 53.46}, 'gaspea_externa': {'35': 55.44, '434': 53.46}}
  Tecido: 8.19 m de 9.99 m

Resultado salvo em resultado_divisao_chat_batidas_inteiras.json
```

Dentro do script [divisao_tonalidades_ergonomico.py](./src/testecloud/chatgpt/divisao_tonalidades_ergonomico.py) é tentado prever as melhores sequencias considerando apenas uma odem de produção de batidas por vez até completar a produção dos pares ja iniciados:

```
Campanhas candidatas de gaspea_interna: 1730
Campanhas candidatas de gaspea_externa: 1878
Status: OPTIMAL

Metros totais: 48.16 m

== tom 1: tamanhos 334, 36, 41, 434, 45 ==
  [gaspea_interna] campanha dos tamanhos 334
      Etapa 1: 5x334  (larg. 121.25 cm) -> 9 batidas x 16.89 cm = 1.52 m
          pares brutos produzidos: 334: 45
  [gaspea_interna] campanha dos tamanhos 36, 41
      Etapa 1: 1x36 + 4x41  (larg. 136.67 cm) -> 27 batidas x 18.69 cm = 5.05 m
          pares brutos produzidos: 36: 27, 41: 108
      Etapa 2: 5x36  (larg. 125.75 cm) -> 7 batidas x 17.23 cm = 1.21 m
          pares brutos produzidos: 36: 35
  [gaspea_interna] campanha dos tamanhos 434, 45
      Etapa 1: 1x434 + 3x45  (larg. 121.07 cm) -> 15 batidas x 20.08 cm = 3.01 m
          pares brutos produzidos: 434: 15, 45: 45
      Etapa 2: 4x434  (larg. 119.48 cm) -> 10 batidas x 19.86 cm = 1.99 m
          pares brutos produzidos: 434: 40
  [gaspea_externa] campanha dos tamanhos 41
      Etapa 1: 5x41  (larg. 137.40 cm) -> 22 batidas x 16.15 cm = 3.55 m
          pares brutos produzidos: 41: 110
  [gaspea_externa] campanha dos tamanhos 334, 45
      Etapa 1: 2x334 + 3x45  (larg. 137.06 cm) -> 15 batidas x 17.27 cm = 2.59 m
          pares brutos produzidos: 334: 30, 45: 45
      Etapa 2: 5x334  (larg. 118.70 cm) -> 3 batidas x 14.47 cm = 0.43 m
          pares brutos produzidos: 334: 15
  [gaspea_externa] campanha dos tamanhos 36, 434
      Etapa 1: 2x36 + 3x434  (larg. 137.26 cm) -> 18 batidas x 17.01 cm = 3.06 m
          pares brutos produzidos: 36: 36, 434: 54
      Etapa 2: 5x36  (larg. 123.70 cm) -> 5 batidas x 14.91 cm = 0.75 m
          pares brutos produzidos: 36: 25
  Produção bruta (pares): {'gaspea_interna': {'334': 45.0, '36': 62.0, '41': 108.0, '434': 55.0, '45': 45.0}, 'gaspea_externa': {'334': 45.0, '36': 61.0, '41': 110.0, '434': 54.0, '45': 45.0}}
  Produção efetiva após 1% de perda: {'gaspea_interna': {'334': 44.55, '36': 61.38, '41': 106.92, '434': 54.45, '45': 44.55}, 'gaspea_externa': {'334': 44.55, '36': 60.39, '41': 108.9, '434': 53.46, '45': 44.55}}
  Tecido: 23.16 m de 40.80 m

== tom 2: tamanhos 35, 378, 40, 42 ==
  [gaspea_interna] campanha dos tamanhos 35, 42
      Etapa 1: 2x35 + 3x42  (larg. 137.46 cm) -> 28 batidas x 19.65 cm = 5.50 m
          pares brutos produzidos: 35: 56, 42: 84
      Etapa 2: 4x42  (larg. 117.12 cm) -> 4 batidas x 19.65 cm = 0.79 m
          pares brutos produzidos: 42: 16
  [gaspea_interna] campanha dos tamanhos 378, 40
      Etapa 1: 1x378 + 4x40  (larg. 136.83 cm) -> 16 batidas x 18.54 cm = 2.97 m
          pares brutos produzidos: 378: 16, 40: 64
      Etapa 2: 5x378  (larg. 133.15 cm) -> 9 batidas x 18.19 cm = 1.64 m
          pares brutos produzidos: 378: 45
  [gaspea_externa] campanha dos tamanhos 35, 42
      Etapa 1: 2x35 + 3x42  (larg. 134.79 cm) -> 28 batidas x 16.76 cm = 4.69 m
          pares brutos produzidos: 35: 56, 42: 84
      Etapa 2: 4x42  (larg. 114.84 cm) -> 4 batidas x 16.76 cm = 0.67 m
          pares brutos produzidos: 42: 16
  [gaspea_externa] campanha dos tamanhos 378, 40
      Etapa 1: 1x378 + 4x40  (larg. 134.28 cm) -> 16 batidas x 16.00 cm = 2.56 m
          pares brutos produzidos: 378: 16, 40: 64
      Etapa 2: 5x378  (larg. 130.40 cm) -> 9 batidas x 15.58 cm = 1.40 m
          pares brutos produzidos: 378: 45
  Produção bruta (pares): {'gaspea_interna': {'35': 56.0, '378': 61.0, '40': 64.0, '42': 100.0}, 'gaspea_externa': {'35': 56.0, '378': 61.0, '40': 64.0, '42': 100.0}}
  Produção efetiva após 1% de perda: {'gaspea_interna': {'35': 55.44, '378': 60.39, '40': 63.36, '42': 99.0}, 'gaspea_externa': {'35': 55.44, '378': 60.39, '40': 63.36, '42': 99.0}}
  Tecido: 20.22 m de 24.70 m

== tom 3: tamanhos 39 ==
  [gaspea_interna] campanha dos tamanhos 39
      Etapa 1: 5x39  (larg. 136.00 cm) -> 14 batidas x 18.39 cm = 2.57 m
          pares brutos produzidos: 39: 70
  [gaspea_externa] campanha dos tamanhos 39
      Etapa 1: 5x39  (larg. 133.25 cm) -> 14 batidas x 15.81 cm = 2.21 m
          pares brutos produzidos: 39: 70
  Produção bruta (pares): {'gaspea_interna': {'39': 70.0}, 'gaspea_externa': {'39': 70.0}}
  Produção efetiva após 1% de perda: {'gaspea_interna': {'39': 69.3}, 'gaspea_externa': {'39': 69.3}}
  Tecido: 4.79 m de 9.99 m

Resultado salvo em resultado_divisao_chat_ergonomico.json
```