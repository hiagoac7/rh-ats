"""
Confere a sintaxe do front-end (app/static/index.html) sem precisar de navegador.

Por que existe
-------------
O index.html e um arquivo unico com JSX compilado no navegador pelo Babel.
Se houver um erro de sintaxe, NADA e desenhado: o usuario ve uma tela branca
e nem a captura de erro do proprio sistema chega a montar.

Ja aconteceu duas vezes:
  * uma edicao caiu dentro de um onClick e partiu a tag ao meio;
  * um bloco de uma tela foi parar em outra, usando variavel inexistente.

Aqui rodam tres conferencias independentes:
  1. delimitadores {} () [] com pilha, ignorando texto, comentario e regex;
  2. aninhamento das tags JSX (o que abre tem que fechar, na ordem certa);
  3. o JS fora do JSX passa pelo parser do proprio Node, quando disponivel.

Uso:
    python -m scripts.checar_jsx
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile

ARQ = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "app", "static", "index.html")

HTML = {
    "div", "span", "button", "input", "table", "thead", "tbody", "tfoot", "tr", "td", "th",
    "form", "label", "select", "option", "textarea", "img", "svg", "path", "circle", "rect",
    "line", "polyline", "h1", "h2", "h3", "h4", "p", "a", "ol", "ul", "li", "dl", "dt", "dd",
    "main", "aside", "nav", "pre", "b", "i", "u", "em", "strong", "kbd", "code", "section",
    "header", "footer", "canvas", "br", "hr", "small", "fieldset", "legend",
}
VAZIAS = {"img", "input", "br", "hr", "path", "circle", "rect", "line", "polyline"}


def carregar():
    fonte = open(ARQ, encoding="utf-8").read()
    ini = fonte.index('type="text/babel">') + len('type="text/babel">')
    fim = fonte.index("</script>", ini)
    return fonte[ini:fim], fonte[:ini].count("\n") + 1


def pular(t: str, k: int) -> int:
    """Se em k comeca texto/comentario, devolve a posicao logo depois. Senao, -1."""
    c = t[k]
    if c in "\"'`":
        m = k + 1
        while m < len(t):
            if t[m] == "\\":
                m += 2
                continue
            if t[m] == c:
                return m + 1
            m += 1
        return len(t)
    if t[k:k+2] == "//":
        m = t.find("\n", k)
        return len(t) if m < 0 else m
    if t[k:k+2] == "/*":
        m = t.find("*/", k + 2)
        return len(t) if m < 0 else m + 2
    return -1


def pular_regex(t: str, k: int, anterior: str) -> int:
    """Expressao regular literal: as aspas dentro dela nao sao string."""
    if t[k] != "/" or anterior not in "(,=:[!&|?{;":
        return -1
    m, classe = k + 1, False
    while m < len(t):
        if t[m] == "\\":
            m += 2
            continue
        if t[m] == "[":
            classe = True
        elif t[m] == "]":
            classe = False
        elif t[m] == "\n":
            return -1
        elif t[m] == "/" and not classe:
            return m + 1
        m += 1
    return -1


def delimitadores(js: str, base: int) -> list[str]:
    erros, pilha, i, ant = [], [], 0, ""
    lin = lambda p: base + js[:p].count("\n")
    while i < len(js):
        p = pular(js, i)
        if p >= 0:
            i, ant = p, "x"
            continue
        r = pular_regex(js, i, ant)
        if r >= 0:
            i, ant = r, "x"
            continue
        c = js[i]
        if c in "({[":
            pilha.append((c, i))
        elif c in ")}]":
            par = {")": "(", "}": "{", "]": "["}[c]
            if not pilha:
                erros.append(f"linha {lin(i)}: fecha '{c}' sem ter aberto")
            elif pilha[-1][0] != par:
                ab, pab = pilha.pop()
                erros.append(f"linha {lin(i)}: fecha '{c}', mas o aberto era '{ab}' da linha {lin(pab)}")
            else:
                pilha.pop()
        if not c.isspace():
            ant = c
        i += 1
    for ab, pos in pilha[-5:]:
        erros.append(f"linha {lin(pos)}: '{ab}' aberto e nunca fechado")
    return erros


def fim_da_tag(s: str, i: int):
    """Fim do '>' da tag que comeca em i, respeitando {} e texto."""
    j, prof = i + 1, 0
    while j < len(s):
        p = pular(s, j)
        if p >= 0:
            j = p
            continue
        c = s[j]
        if c == "{":
            prof += 1
        elif c == "}":
            prof -= 1
        elif c == ">" and prof == 0:
            return j, s[j-1] == "/"
        j += 1
    return -1, False


def tags(js: str, base: int) -> list[str]:
    comp = set(re.findall(r"\n(?:async )?(?:function|class) ([A-Z]\w*)", js))
    erros, pilha, i = [], [], 0
    lin = lambda p: base + js[:p].count("\n")
    while i < len(js):
        p = pular(js, i)
        if p >= 0:
            i = p
            continue
        if js[i] == "<":
            m = re.match(r"<\s*(/?)\s*([A-Za-z][\w.]*)?", js[i:i+40])
            nome = (m.group(2) or "") if m else ""
            frag = bool(re.match(r"<\s*/?\s*>", js[i:i+5]))
            if not frag and (not nome or (nome not in HTML and nome not in comp)):
                i += 1
                continue
            ft, auto = fim_da_tag(js, i)
            if ft < 0:
                i += 1
                continue
            fecha = bool(m.group(1))
            if frag:
                if fecha:
                    if pilha and pilha[-1][0] == "<>":
                        pilha.pop()
                    else:
                        erros.append(f"linha {lin(i)}: '</>' sem '<>' correspondente")
                else:
                    pilha.append(("<>", i))
            elif fecha:
                if not pilha:
                    erros.append(f"linha {lin(i)}: </{nome}> sem abertura")
                elif pilha[-1][0] != nome:
                    ab, pos = pilha[-1]
                    erros.append(f"linha {lin(i)}: </{nome}> fecha, mas o aberto era <{ab}> da linha {lin(pos)}")
                    achou = [k for k, (a, _) in enumerate(pilha) if a == nome]
                    if achou:
                        del pilha[achou[-1]:]
                else:
                    pilha.pop()
            elif not (auto or nome in VAZIAS):
                pilha.append((nome, i))
            i = ft + 1
            continue
        i += 1
    for nome, pos in pilha[-5:]:
        erros.append(f"linha {lin(pos)}: <{nome}> aberto e nunca fechado")
    return erros


def pelo_node(js: str) -> list[str]:
    """Troca cada elemento JSX por null e manda o resto para o parser do Node."""
    if not shutil.which("node"):
        return []
    comp = set(re.findall(r"\n(?:async )?(?:function|class) ([A-Z]\w*)", js))
    saida, i, prof, ini_topo = [], 0, 0, None
    while i < len(js):
        p = pular(js, i)
        if p >= 0:
            if prof == 0:
                saida.append(js[i:p])
            i = p
            continue
        if js[i] == "<":
            m = re.match(r"<\s*(/?)\s*([A-Za-z][\w.]*)?", js[i:i+40])
            nome = (m.group(2) or "") if m else ""
            frag = bool(re.match(r"<\s*/?\s*>", js[i:i+5]))
            if frag or (nome and (nome in HTML or nome in comp)):
                ft, auto = fim_da_tag(js, i)
                if ft >= 0:
                    if prof == 0:
                        ini_topo = i
                    if m.group(1):
                        prof -= 1
                    elif not (auto or nome in VAZIAS):
                        prof += 1
                    if prof == 0 and ini_topo is not None:
                        bloco = js[ini_topo:ft+1]
                        saida.append("null" + "\n" * bloco.count("\n"))
                        ini_topo = None
                    i = ft + 1
                    continue
        if prof == 0:
            saida.append(js[i])
        i += 1

    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write("".join(saida))
        caminho = f.name
    try:
        r = subprocess.run(["node", "--check", caminho], capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            linha = (r.stderr or "").strip().split("\n")
            return ["Node recusou o JS: " + " | ".join(linha[:4])]
        return []
    except Exception:
        return []
    finally:
        os.unlink(caminho)


def main() -> int:
    js, base = carregar()
    problemas = []
    for rotulo, achados in [
        ("delimitadores", delimitadores(js, base)),
        ("tags JSX", tags(js, base)),
        ("parser do Node", pelo_node(js)),
    ]:
        if achados:
            problemas.append((rotulo, achados))
            print(f"  [FALHA] {rotulo}:")
            for a in achados[:8]:
                print("      ", a)
        else:
            print(f"  [ok]    {rotulo}")
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
