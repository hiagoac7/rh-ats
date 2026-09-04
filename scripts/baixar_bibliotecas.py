"""
Traz as bibliotecas de fora para dentro do projeto.

Por que isto existe
-------------------
O front-end usava React, ReactDOM, Babel, Tailwind e Chart.js baixando tudo da
internet (unpkg.com, cdn.tailwindcss.com, cdnjs.com) A CADA vez que a pagina
abria. Consequencia: sem internet, com firewall da empresa bloqueando, ou com
o CDN fora do ar, o sistema simplesmente nao abre — tela branca.

Para um sistema interno de RH isso e inaceitavel. Depois de rodar este script,
os arquivos ficam em app/static/vendor/ e sao servidos pelo proprio servidor.

Como usar
---------
    python -m scripts.baixar_bibliotecas

Rode uma vez, num computador com internet. Depois pode copiar a pasta inteira
para maquinas sem acesso externo.
"""
from __future__ import annotations

import hashlib
import os
import sys
import urllib.request

PASTA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "app", "static", "vendor")

BIBLIOTECAS = [
    ("react.production.min.js",
     "https://unpkg.com/react@18.3.1/umd/react.production.min.js", 100),
    ("react-dom.production.min.js",
     "https://unpkg.com/react-dom@18.3.1/umd/react-dom.production.min.js", 100),
    ("babel.min.js",
     "https://unpkg.com/@babel/standalone@7.26.4/babel.min.js", 1000),
    ("tailwind.js",
     "https://cdn.tailwindcss.com/3.4.16", 200),
    ("chart.umd.min.js",
     "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js", 100),
]


def baixar(url: str, minimo_kb: int) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "ATS-TLM/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        dados = r.read()
    kb = len(dados) / 1024
    if kb < minimo_kb:
        raise RuntimeError(
            f"veio pequeno demais ({kb:.0f} KB, esperado ao menos {minimo_kb} KB). "
            "Pode ser uma pagina de erro do proxy da empresa em vez do arquivo."
        )
    inicio = dados[:200].lstrip().lower()
    if inicio.startswith(b"<!doctype") or inicio.startswith(b"<html"):
        raise RuntimeError("veio uma pagina HTML no lugar do arquivo (bloqueio de rede?).")
    return dados


def main() -> int:
    os.makedirs(PASTA, exist_ok=True)
    print("=" * 60)
    print("  Trazendo as bibliotecas para dentro do projeto")
    print("=" * 60)
    print(f"  Destino: {PASTA}\n")

    falhas = []
    for nome, url, minimo in BIBLIOTECAS:
        destino = os.path.join(PASTA, nome)
        print(f"  {nome:32} ", end="", flush=True)
        try:
            dados = baixar(url, minimo)
        except Exception as e:
            if os.path.exists(destino):
                print(f"FALHOU ({e}) — mantendo a copia que ja existia")
            else:
                print(f"FALHOU: {e}")
                falhas.append(nome)
            continue
        with open(destino, "wb") as f:
            f.write(dados)
        soma = hashlib.sha256(dados).hexdigest()[:12]
        print(f"ok  {len(dados)/1024:7.0f} KB  sha256:{soma}")

    print()
    if falhas:
        print("=" * 60)
        print("  NEM TUDO FOI BAIXADO")
        print("=" * 60)
        print("  Faltaram:", ", ".join(falhas))
        print()
        print("  O sistema continua funcionando: o que faltar e buscado na")
        print("  internet, como antes. Rode de novo com internet liberada")
        print("  para completar.")
        return 1

    print("=" * 60)
    print("  TUDO PRONTO")
    print("=" * 60)
    print("  O sistema agora abre sem depender da internet.")
    print("  Reinicie o iniciar.bat e atualize a pagina com Ctrl+Shift+R.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
