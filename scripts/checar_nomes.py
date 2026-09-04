"""Verifica se algum nome é usado ANTES de ser importado/definido (erro que py_compile não pega)."""
import ast, sys, glob, builtins

BUILTINS = set(dir(builtins))

def checar(caminho):
    src = open(caminho, encoding="utf-8").read()
    arv = ast.parse(src)
    definidos = {}
    problemas = []

    for no in ast.walk(arv):
        if isinstance(no, (ast.Import, ast.ImportFrom)):
            for a in no.names:
                nome = a.asname or a.name.split(".")[0]
                definidos.setdefault(nome, no.lineno)
        elif isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            definidos.setdefault(no.name, no.lineno)
        elif isinstance(no, ast.Assign):
            for alvo in no.targets:
                if isinstance(alvo, ast.Name):
                    definidos.setdefault(alvo.id, no.lineno)

    for no in ast.walk(arv):
        if isinstance(no, ast.ClassDef):
            for filho in ast.walk(no):
                if isinstance(filho, ast.Name) and isinstance(filho.ctx, ast.Load):
                    n = filho.id
                    if n in BUILTINS or n in ("self", "cls"):
                        continue
                    linha_def = definidos.get(n)
                    if linha_def is None:
                        continue
                    if linha_def > filho.lineno:
                        problemas.append((filho.lineno, n, linha_def, no.name))
    return problemas

falhou = False
for f in sorted(glob.glob("app/**/*.py", recursive=True) + glob.glob("scripts/*.py")):
    p = checar(f)
    if p:
        falhou = True
        for linha, nome, ldef, classe in p:
            print(f"  {f}:{linha}  '{nome}' usado na classe {classe}, mas só existe na linha {ldef}")
print("RESULTADO:", "PROBLEMA ENCONTRADO" if falhou else "nenhum nome usado antes de existir")
sys.exit(1 if falhou else 0)
