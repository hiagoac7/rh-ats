"""
Verificação completa do sistema — roda sem precisar do banco nem das bibliotecas.
Uso:  python scripts/verificar.py
"""
import ast, glob, os, re, sys, builtins

FALHAS = []
def ok(msg):    print(f"  [ok]    {msg}")
def falha(msg): FALHAS.append(msg); print(f"  [FALHA] {msg}")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)

print("=" * 60)
print("  VERIFICAÇÃO DO SISTEMA ATS")
print("=" * 60)

print("\n1) Sintaxe dos arquivos Python")
for f in glob.glob("app/**/*.py", recursive=True) + glob.glob("scripts/*.py") + glob.glob("migrations/**/*.py", recursive=True):
    try:
        ast.parse(open(f, encoding="utf-8").read())
    except SyntaxError as e:
        falha(f"{f}: {e}")
else:
    if not FALHAS: ok("todos os arquivos compilam")

print("\n2) Nomes usados antes de serem importados")
BUILT = set(dir(builtins))
achou = False
for f in glob.glob("app/**/*.py", recursive=True):
    arv = ast.parse(open(f, encoding="utf-8").read())
    definidos = {}
    for no in ast.walk(arv):
        if isinstance(no, (ast.Import, ast.ImportFrom)):
            for a in no.names:
                definidos.setdefault(a.asname or a.name.split(".")[0], no.lineno)
        elif isinstance(no, (ast.FunctionDef, ast.ClassDef)):
            definidos.setdefault(no.name, no.lineno)
    for no in ast.walk(arv):
        if isinstance(no, ast.ClassDef):
            for filho in ast.walk(no):
                if isinstance(filho, ast.Name) and isinstance(filho.ctx, ast.Load):
                    ld = definidos.get(filho.id)
                    if ld and ld > filho.lineno:
                        falha(f"{f}:{filho.lineno} '{filho.id}' usado antes da linha {ld}"); achou = True
if not achou: ok("nenhum nome usado antes de existir")

print("\n3) Routers registrados na aplicação")
main = open("app/main.py", encoding="utf-8").read()
arqs = {os.path.basename(f)[:-3] for f in glob.glob("app/routers/*.py")} - {"__init__"}
reg = set(re.findall(r"app\.include_router\((\w+)\.router\)", main))
if arqs - reg: falha(f"routers não registrados: {sorted(arqs - reg)}")
else: ok(f"{len(arqs)} routers registrados")

print("\n4) Endpoints exigem autenticação")
publicos = {"/auth/login", "/versao"}
livres = []
for f in glob.glob("app/routers/*.py"):
    src = open(f, encoding="utf-8").read()
    pref = re.search(r'prefix="([^"]*)"', src)
    pref = pref.group(1) if pref else ""
    prot_router = bool(re.search(r"dependencies=\[Depends\((require_perm|get_current_user)", src))
    for m in re.finditer(r'@router\.(get|post|patch|delete)\("([^"]*)"[^)]*\)\s*\ndef \w+\(([\s\S]*?)\):', src):
        caminho = f"{pref}{m.group(2)}" or "/"
        if caminho in publicos: continue
        if not (prot_router or "require_perm" in m.group(3) or "get_current_user" in m.group(3)):
            livres.append(f"{m.group(1).upper()} {caminho}")
if livres: falha(f"endpoints sem proteção: {livres}")
else: ok("todos os endpoints exigem login/permissão")

print("\n4b) Rota assincrona nao trava o servidor")
_travam = []
for _f in sorted(glob.glob("app/routers/*.py")):
    _src = open(_f, encoding="utf-8").read()
    for _m in re.finditer(r"\nasync def (\w+)\(([\s\S]*?)(?=\n@router|\Z)", _src):
        _corpo = _m.group(0)
        for _laco in re.finditer(r"\n(\s+)(while|for)\b[^\n]*:\n", _corpo):
            _rec = len(_laco.group(1))
            _resto = _corpo[_laco.end():]
            _dentro = []
            for _l in _resto.split("\n"):
                if _l.strip() and (len(_l) - len(_l.lstrip())) <= _rec:
                    break
                _dentro.append(_l)
            _bloco = "\n".join(_dentro)
            _bloco = re.sub(r"(to_thread|run_in_executor)\([^)]*\)", "", _bloco)
            if re.search(r"db\.(scalars|scalar|query|execute|get|commit|add)\(", _bloco) or \
               re.search(r"\b\w+\.\w+\(\s*db\s*[,)]", _bloco):
                _travam.append(f"{os.path.basename(_f)}: {_m.group(1)}()")
                break
if _travam:
    falha("rota assincrona consultando o banco dentro de laco (trava o servidor sob carga): "
          + ", ".join(sorted(set(_travam))))
else:
    ok("nenhuma rota assincrona bloqueia o laco de eventos")

print("\n5) Cadeia de migrations")
revs = {}
for f in glob.glob("migrations/versions/*.py"):
    s = open(f, encoding="utf-8").read()
    r = re.search(r'^revision = "(\w+)"', s, re.M)
    d = re.search(r'^down_revision = (?:None|"(\w+)")', s, re.M)
    if r: revs[r.group(1)] = d.group(1) if d and d.group(1) else None
raizes = [r for r, d in revs.items() if d is None]
if len(raizes) != 1: falha(f"deveria haver 1 migration raiz, há {len(raizes)}")
else:
    cadeia, atual = [], raizes[0]
    while atual:
        cadeia.append(atual)
        prox = [r for r, d in revs.items() if d == atual]
        if len(prox) > 1: falha(f"bifurcação em {atual}"); break
        atual = prox[0] if prox else None
    if len(cadeia) == len(revs): ok(f"{len(revs)} migrations em cadeia contínua")
    else: falha(f"migrations soltas: {sorted(set(revs) - set(cadeia))}")

print("\n6) Migrations cobrem as colunas dos models")
mod = open("app/models.py", encoding="utf-8").read()
tabelas = {}
for m in re.finditer(r'__tablename__ = "(\w+)"(.*?)(?=\n\nclass |\Z)', mod, re.S):
    tabelas[m.group(1)] = set(re.findall(r"^\s{4}(\w+):\s*Mapped\[[^\]]*\]\s*=\s*mapped_column", m.group(2), re.M))
mig = "".join(open(f, encoding="utf-8").read() for f in glob.glob("migrations/versions/*.py"))
criadas = {}
for m in re.finditer(r'op\.create_table\(\s*"(\w+)",(.*?)\n    \)', mig, re.S):
    criadas[m.group(1)] = set(re.findall(r'sa\.Column\("(\w+)"', m.group(2)))
for m in re.finditer(r'op\.add_column\("(\w+)",\s*sa\.Column\("(\w+)"', mig):
    criadas.setdefault(m.group(1), set()).add(m.group(2))
faltas = {t: sorted(c - criadas.get(t, set())) for t, c in tabelas.items() if c - criadas.get(t, set())}
if faltas: falha(f"colunas sem migration: {faltas}")
else: ok(f"{len(tabelas)} tabelas cobertas")

print("\n7) Campos dos schemas existem nos models")
sch = open("app/schemas.py", encoding="utf-8").read()
IGN = {"senha", "senha_atual", "senha_nova", "permissoes", "dias_parado",
       "confirmar_pendencias", "confirmar_duplicado"}
def campos_sch(n):
    m = re.search(rf"class {n}\(([^)]*)\):(.*?)(?=\nclass |\Z)", sch, re.S)
    if not m: return set()
    f = set(re.findall(r"^\s{4}(\w+):", m.group(2), re.M))
    if m.group(1).strip().endswith("Base"): f |= campos_sch(m.group(1).strip())
    return f
def cols_mod(n):
    m = re.search(rf"class {n}\(Base\):(.*?)(?=\n\nclass |\Z)", mod, re.S)
    return set(re.findall(r"^\s{4}(\w+):\s*Mapped", m.group(1), re.M)) if m else set()
prob = []
for esq, mdl in [("CandidatoCreate","Candidato"),("CandidatoUpdate","Candidato"),("VagaCreate","Vaga"),
                 ("VagaUpdate","Vaga"),("CanalCreate","Canal"),("CanalUpdate","Canal"),
                 ("ListaCreate","Lista"),("ListaUpdate","Lista"),("CampoCreate","CampoPersonalizado")]:
    extra = campos_sch(esq) - cols_mod(mdl) - IGN
    if extra: prob.append(f"{esq}: {sorted(extra)}")
if prob: falha(f"campos inexistentes: {prob}")
else: ok("schemas e models alinhados")

print("\n8) Front-end (index.html)")
h = open("app/static/index.html", encoding="utf-8").read()
js = h.split('type="text/babel">')[1].split("</script>")[0]
for par, a, b in [("chaves","{","}"), ("parênteses","(",")"), ("colchetes","[","]")]:
    if js.count(a) != js.count(b): falha(f"{par} desbalanceados")
if js.count("<>") != js.count("</>"): falha("fragmentos <> desbalanceados")
mau = []
for t in ["div","span","form","button","table","thead","tbody","tr","td","th","label","dl","dt","dd","main","aside","nav","p","h1","h2","h3","a","select","textarea"]:
    ab = len(re.findall(rf"<{t}\b", js)); fe = len(re.findall(rf"</{t}>", js))
    au = len(re.findall(rf"<{t}\b[^>]*/>", js))
    if ab - au - fe: mau.append(t)
if mau: falha(f"tags desbalanceadas: {mau}")
comp = set(re.findall(r"function ([A-Z]\w+)\s*\(", js)) | set(re.findall(r"const ([A-Z]\w+)\s*=\s*\(?\{", js))
comp |= set(re.findall(r"class ([A-Z]\w+)\s+extends", js))
comp |= set(re.findall(r"const ([A-Z]\w+)\s*=\s*\(", js))
usados = set(re.findall(r"<([A-Z]\w+)[\s/>]", js)) - {"React"}
if usados - comp: falha(f"componentes usados sem definição: {sorted(usados - comp)}")
ic = set(re.findall(r"^\s{2}(\w+):\s*\[", js, re.M))
alias = set(re.findall(r'(\w+):"', js.split("const ALIAS")[1].split("};")[0])) if "const ALIAS" in js else set()
usic = set(re.findall(r'<Icon name="(\w+)"', js)) | set(re.findall(r'icon="(\w+)"', js)) | set(re.findall(r'abas\.push\(\["\w+","[^"]+","(\w+)"\]\)', js))
if usic - ic - alias: falha(f"ícones inexistentes: {sorted(usic - ic - alias)}")
_g = re.search(r"const GRUPOS\s*=\s*\[([\s\S]*?)\]\.map\(", js)
if _g:
    abas = set(re.findall(r'\["(\w+)","[^"]+","\w+",', _g.group(1)))
else:
    abas = set(re.findall(r'abas\.push\(\["(\w+)"', js))
rend = set(a for a, _ in re.findall(r'aba==="(\w+)"&&<(\w+)', js))
if abas - rend: falha(f"abas sem tela: {sorted(abas - rend)}")
if rend - abas: falha(f"telas sem aba: {sorted(rend - abas)}")
if not any(f.startswith(("chaves","parênteses","colchetes","fragmentos","tags","componentes","ícones","abas","telas")) for f in FALHAS):
    ok(f"{len(comp)} componentes, {len(abas)} abas, tags e delimitadores equilibrados")

print("\n8b) Hooks do React no lugar certo")
blocos = re.split(r"\nfunction ([A-Z]\w+)\s*\(", js)
maus = []
for i in range(1, len(blocos), 2):
    nome = blocos[i]; corpo = blocos[i + 1].split("\nfunction ")[0]
    linhas = corpo.split("\n"); ret = None
    for n, l in enumerate(linhas):
        if re.match(r"  (if\s*\(.*\)\s*)?return[\s(<]", l) and not l.startswith("   ") and ret is None:
            ret = n
        if re.match(r"  (const|let|var)?\s*\[?[\w,\s{}]*\]?\s*=?\s*"
                    r"use(State|Effect|Ref|Memo|Callback|Relogio|Sincronizar|Preferencia|Ordenacao)\(", l) \
           and not l.startswith("   ") and ret is not None:
            maus.append(f"{nome} (hook após return, linha {n})"); break
if maus: falha(f"hooks fora de lugar — quebram a tela: {maus}")
else: ok("todos os hooks vêm antes dos returns")

print("\n8c) Carregamento inicial reage ao login")
def _corpo_do_efeito(texto, inicio):
    """De 'useEffect(' ate o ')' final. Devolve (corpo, deps) ou None."""
    p = texto.find("{", inicio)
    if p < 0:
        return None
    prof, k = 0, p
    while k < len(texto):
        if texto[k] == "{":
            prof += 1
        elif texto[k] == "}":
            prof -= 1
            if prof == 0:
                break
        k += 1
    if prof != 0:
        return None
    corpo = texto[p:k+1]
    resto = texto[k+1:k+80]
    m = re.match(r"\s*,\s*\[([^\]]*)\]", resto)
    return corpo, (m.group(1).strip() if m else None)

presos, ilegiveis = [], 0
for m in re.finditer(r"useEffect\(", js):
    achado = _corpo_do_efeito(js, m.end())
    if achado is None:
        ilegiveis += 1
        continue
    corpo, deps = achado
    if deps is None:
        continue
    if ("S.token()" in corpo or "logado" in corpo) and "logado" not in deps:
        antes = js[max(0, m.start()-300):m.start()]
        nomes = re.findall(r"function (\w+)\s*\(", antes)
        presos.append(nomes[-1] if nomes else f"linha {js[:m.start()].count(chr(10))+1}")
if ilegiveis:
    falha(f"{ilegiveis} useEffect que nao consegui ler — a checagem ficaria cega")
elif presos:
    falha(f"carregamento que só roda antes do login (tela fica em 'Carregando'): {presos}")
else:
    ok("nenhum carregamento preso — a tela abre sem precisar de F5")

print("\n8d) Funções usadas nos componentes existem")
comps = [(m.group(1), m.start()) for m in re.finditer(r"\nfunction ([A-Z]\w*)\s*\(", js)]
fantasmas = []
for i, (nome, pos) in enumerate(comps):
    corpo = js[pos:(comps[i + 1][1] if i + 1 < len(comps) else len(js))]
    for m in re.finditer(r"useSincronizar\(\s*([A-Za-z_]\w*)", corpo):
        fn = m.group(1)
        if not re.search(r"\b(function\s+%s\b|const\s+%s\s*=|let\s+%s\s*=)" % (fn, fn, fn), corpo):
            fantasmas.append(f"{nome} chama {fn}()")
if fantasmas:
    falha("função inexistente — a tela quebra ao abrir: " + "; ".join(fantasmas))
else:
    ok("nenhuma chamada a função inexistente nos componentes")

print("\n8f) Estado de um componente nao vaza para outro")
_comps = [(m.group(1), m.start()) for m in re.finditer(r"\n(?:async )?(?:function|class) (\w+)\b", js)]
_corpos, _estados = {}, {}
for _k, (_n, _p) in enumerate(_comps):
    _f = _comps[_k + 1][1] if _k + 1 < len(_comps) else len(js)
    _corpos[_n] = js[_p:_f]
    _estados[_n] = set(re.findall(r"\[\s*(\w+)\s*,\s*set\w+\s*\]\s*=\s*useState", _corpos[_n]))
_donos = {}
for _c, _e in _estados.items():
    for _v in _e: _donos.setdefault(_v, set()).add(_c)
_vazou = []
for _n, _corpo in _corpos.items():
    if _corpo.lstrip().startswith("class ") or not _n[0].isupper():
        continue
    _loc = set(re.findall(r"(?:const|let|var)\s+(\w+)", _corpo))
    _loc |= set(re.findall(r"function\s+(\w+)", _corpo))
    _loc |= set(re.findall(r"(\w+)\s*=>", _corpo))
    for _m in re.finditer(r"\(([\w,\s]*)\)\s*=>", _corpo):
        _loc |= {x.strip() for x in _m.group(1).split(",") if x.strip()}
    for _m in re.finditer(r"\[([^\]]+)\]\s*=\s*useState", _corpo):
        _loc |= {x.strip().split("=")[0].strip() for x in _m.group(1).split(",") if x.strip()}
    for _m in re.finditer(r"(?:const|let|var)\s*\[([^\]]+)\]", _corpo):
        _loc |= {x.strip().split("=")[0].strip() for x in _m.group(1).split(",") if x.strip()}
    for _m in re.finditer(r"(?:const|let|var)\s*\{([^}]+)\}", _corpo):
        _loc |= {x.strip().split(":")[-1].split("=")[0].strip() for x in _m.group(1).split(",") if x.strip()}
    for _m in re.finditer(r"\(\s*\[([^\]]+)\]\s*\)\s*=>", _corpo):
        _loc |= {x.strip() for x in _m.group(1).split(",") if x.strip()}
    for _m in re.finditer(r"\(\s*\{([^}]+)\}\s*\)\s*=>", _corpo):
        _loc |= {x.strip().split(":")[-1].split("=")[0].strip() for x in _m.group(1).split(",") if x.strip()}
    for _m in re.finditer(r"(?:const|let|var)\s+([^;\n]+)", _corpo):
        for _parte in _m.group(1).split(","):
            _d = re.match(r"\s*(\w+)\s*=", _parte)
            if _d: _loc.add(_d.group(1))
    _cab = re.search(r"function \w+\s*\(([\s\S]*?)\)\s*\{", _corpo)
    if _cab: _loc |= set(re.findall(r"\w+", _cab.group(1)))
    _limpo = re.sub(r'"[^"]*"|\'[^\']*\'|`[^`]*`', '""', _corpo)
    _limpo = re.sub(r"/\*[\s\S]*?\*/", " ", _limpo)
    _limpo = re.sub(r"//[^\n]*", " ", _limpo)
    _limpo = re.sub(r">[^<>{}]*<", "><", _limpo)
    _limpo = re.sub(r"\}[^<>{}]*<", "}<", _limpo)
    _limpo = re.sub(r">[^<>{}]*\{", ">{", _limpo)
    for _v, _dono in _donos.items():
        if _n in _dono or _v in _loc:
            continue
        if re.search(r"[{(\s!]" + re.escape(_v) + r"\s*[.\[]|\{\s*" + re.escape(_v) + r"\s*\}", _limpo):
            _vazou.append(f"{_n} usa '{_v}' (estado de {', '.join(sorted(_dono))})")
if _vazou:
    falha("estado usado fora do componente — a tela quebra ao abrir: " + "; ".join(_vazou))
else:
    ok("nenhum estado usado fora do seu componente")

print("\n8k) Nenhum componente definido duas vezes")
_nomes = re.findall(r"\n(?:async )?function ([A-Z]\w*)\s*\(", js)
_dobrados = sorted({n for n in _nomes if _nomes.count(n) > 1})
if _dobrados:
    falha(f"componente definido mais de uma vez (a segunda apaga a primeira): {_dobrados}")
else:
    ok(f"{len(set(_nomes))} componentes, cada um definido uma vez so")

print("\n8j) Versao do servidor e da tela combinam")
_vpy = re.search(r'VERSAO\s*=\s*"([^"]+)"', open("app/versao.py", encoding="utf-8").read())
_vjs = re.search(r'VERSAO_TELA\s*=\s*"([^"]+)"', h)
if not _vpy or not _vjs:
    falha("nao achei a versao em app/versao.py ou no index.html")
elif _vpy.group(1) != _vjs.group(1):
    falha(f"versoes diferentes: servidor {_vpy.group(1)} x tela {_vjs.group(1)} "
          "— o aviso de 'reinicie o servidor' apareceria sem motivo")
else:
    ok(f"versao {_vpy.group(1)} nos dois lados")

print("\n8h) Bibliotecas nao dependem so da internet")
_cab = h[:h.find("<style>")]
_locais = re.findall(r'<script src="/static/vendor/([\w.-]+)"></script>', _cab)
_reservas = re.findall(r'window\.(\w+)\|\|document\.write', _cab)
if not _locais:
    falha("o front nao usa a pasta vendor: qualquer queda de CDN deixa a tela branca")
elif len(_locais) != len(_reservas):
    falha(f"{len(_locais)} bibliotecas locais mas {len(_reservas)} linhas de reserva — "
          "sem reserva, faltar o arquivo local apaga a tela")
else:
    ok(f"{len(_locais)} bibliotecas servidas localmente, todas com reserva na internet")

print("\n8i) Sintaxe do front conferida a fundo")
try:
    import importlib.util as _iu
    _spec = _iu.spec_from_file_location(
        "checar_jsx", os.path.join(os.path.dirname(os.path.abspath(__file__)), "checar_jsx.py"))
    _cj = _iu.module_from_spec(_spec); _spec.loader.exec_module(_cj)
    _js, _base = _cj.carregar()
    _achados = _cj.delimitadores(_js, _base) + _cj.tags(_js, _base) + _cj.pelo_node(_js)
    if _achados:
        falha("sintaxe do front: " + " | ".join(_achados[:4]))
    else:
        ok("delimitadores, tags e parser do Node de acordo")
except Exception as _e:
    falha(f"nao consegui conferir a sintaxe do front: {_e}")

print("\n8g) Nenhuma tag JSX foi partida ao meio")
def _pula(t, k):
    ch = t[k]
    if ch in "\"'`":
        m = k + 1
        while m < len(t):
            if t[m] == "\\": m += 2; continue
            if t[m] == ch: return m + 1
            m += 1
        return len(t)
    if t[k:k+2] == "//":
        m = t.find("\n", k); return len(t) if m < 0 else m
    if t[k:k+2] == "/*":
        m = t.find("*/", k+2); return len(t) if m < 0 else m+2
    return -1

_partidas = []
_k, _n = 0, len(js)
while _k < _n:
    _p = _pula(js, _k)
    if _p >= 0: _k = _p; continue
    if js[_k] == "<" and re.match(r"<\s*[A-Za-z][\w.]*", js[_k:_k+40]):
        _j, _prof, _miolo = _k+1, 0, []
        while _j < _n:
            _q = _pula(js, _j)
            if _q >= 0: _j = _q; continue
            _c = js[_j]
            if _c == "{": _prof += 1
            elif _c == "}": _prof -= 1
            elif _c == ">" and _prof == 0: break
            if _prof > 0: _miolo.append(_c)
            _j += 1
        if re.search(r"</\s*[A-Za-z][\w.]*\s*>\s*[A-Za-z_$]", "".join(_miolo)):
            _partidas.append(js[:_k].count("\n") + 1)
        _k = _j + 1; continue
    _k += 1
if _partidas:
    falha("tag JSX partida ao meio — a tela inteira nao abre; linhas do script: " + str(_partidas[:8]))
else:
    ok("nenhuma tag JSX partida")

print("\n8e) Arquivos .bat aguentam nome com parentese")
bat_ruins = []
for arq in sorted(glob.glob("*.bat")):
    txt = open(arq, encoding="utf-8", errors="replace").read()
    livres = set(re.findall(r'set\s+"?(\w+)=%~1', txt))
    livres |= set(re.findall(r'set\s+"?(\w+)=%%~?\w+', txt))
    livres |= set(re.findall(r'set\s*/p\s+"?(\w+)=', txt))
    livres |= set(re.findall(r'set\s+"(\w+)=[%!][A-Za-z_]', txt))
    livres -= set(re.findall(r'set\s+"?(\w+)=%(?:ERRORLEVEL|errorlevel|date|time|DATA|HORA)', txt))
    livres -= {"CODIGO", "DATA", "HORA", "OPCAO"}
    if not livres:
        continue
    for blk in re.finditer(r'\(\s*\r?\n((?:[^()\r\n]*\r?\n)*?)\s*\)', txt):
        for linha in blk.group(1).splitlines():
            if linha.strip().lower().startswith("rem"):
                continue
            sem_aspas = re.sub(r'"[^"]*"', "", linha)
            for v in re.findall(r'[%!](\w+)[%!]', sem_aspas):
                if v in livres:
                    bat_ruins.append(f"{arq}: {linha.strip()}")
if bat_ruins:
    falha("variavel sem aspas dentro de bloco — a janela fecha sozinha: " + " | ".join(dict.fromkeys(bat_ruins)))
else:
    ok("nenhum .bat quebra com parentese no nome do arquivo")

print("\n9) Chamadas do front existem na API")
back = []
_main = open("app/main.py", encoding="utf-8").read()
for m in re.finditer(r'@app\.(get|post|patch|delete)\("([^"]*)"', _main):
    back.append(re.sub(r"\{[^}]+\}", "*", m.group(2) or "/"))
for f in glob.glob("app/routers/*.py"):
    src = open(f, encoding="utf-8").read()
    pref = re.search(r'prefix="([^"]*)"', src)
    pref = pref.group(1) if pref else ""
    for m in re.finditer(r'@router\.(get|post|patch|delete)\("([^"]*)"', src):
        back.append(re.sub(r"\{[^}]+\}", "*", (pref + m.group(2)) or "/"))
def existe(rota):
    alvo = rota.split("?")[0].rstrip("/")
    for r in back:
        if re.fullmatch(r.replace("*", "[^/]*"), alvo) or re.fullmatch(r.replace("*", "[^/]*"), alvo + "/x"):
            return True
    return False
chamadas = set(re.findall(r'getJSON\("([^"]+)"', js)) | set(re.findall(r'sendJSON\("([^"]+)"', js)) \
         | set(re.findall(r'api\("([^"]+)"', js)) | set(re.findall(r'fetch\(API\+"([^"]+)"', js))
ruins = [c for c in chamadas if not existe(c)]
if ruins: falha(f"rotas chamadas que não existem: {sorted(ruins)}")
else: ok(f"{len(chamadas)} chamadas conferidas")

print("\n" + "=" * 60)
if FALHAS:
    print(f"  {len(FALHAS)} PROBLEMA(S) ENCONTRADO(S)")
    sys.exit(1)
print("  TUDO CERTO — nenhum problema encontrado")
print("=" * 60)
