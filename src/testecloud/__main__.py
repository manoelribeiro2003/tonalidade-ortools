from .claude.divisao_tonalidades import resolver, imprimir
import json

if __name__ == "__main__":
    res = resolver()
    if res:
        imprimir(res)
        with open("resultado_divisao.json", "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
        print("Resultado salvo em resultado_divisao.json")