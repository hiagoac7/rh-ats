"""
API do sistema interno de R&S (ATS) - TLM Equipamentos.

Rodar:
    uvicorn app.main:app --reload
Docs interativas:
    http://localhost:8000/docs
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from . import models
from . import eventos
from .routers import auth, vagas, candidatos, ciclos, painel, fila, gestores, auditoria, anotacoes, canais, listas, exportar, campos, mensagens, requisicoes, acessos, tempo_real, busca

from .database import DATABASE_URL
from .esquema import preparar

if DATABASE_URL.startswith("sqlite"):
    preparar()

app = FastAPI(
    title="ATS - Recrutamento e Selecao TLM",
    description="API interna de R&S. Substitui a planilha Automacao_RH.",
    version="0.1.0",
)

from .versao import VERSAO


@app.get("/versao", tags=["Sistema"])
def versao():
    """
    Publico de proposito: a tela consulta isto ANTES de qualquer login, para
    avisar quando o servidor ficou para tras depois de uma atualizacao.
    Nao expoe nada sensivel — so o numero da versao.
    """
    return {"versao": VERSAO}


@app.exception_handler(Exception)
async def erro_inesperado(request, exc):
    """
    Rede de seguranca para o que ninguem previu.

    Sem isto, um erro nao tratado devolve o rastro da excecao para o navegador
    — o que expoe caminhos de arquivo e nomes de tabela — e a tela mostra uma
    mensagem incompreensivel. Aqui o detalhe fica no log do servidor e o
    usuario recebe algo que ele consegue repassar ao TI.
    """
    import logging
    import uuid
    codigo = uuid.uuid4().hex[:8]
    logging.getLogger("ats").exception("[%s] %s %s", codigo, request.method, request.url.path)
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": f"Algo deu errado do lado do servidor. "
                           f"Informe ao TI o codigo {codigo}."},
    )


LIMITE_ENVIO = int(os.getenv("LIMITE_ENVIO_MB", "12")) * 1024 * 1024


@app.middleware("http")
async def limitar_tamanho(request, call_next):
    tamanho = request.headers.get("content-length")
    if tamanho and tamanho.isdigit() and int(tamanho) > LIMITE_ENVIO:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=413,
            content={"detail": f"Envio grande demais. O limite e "
                               f"{LIMITE_ENVIO // (1024*1024)} MB."},
        )
    return await call_next(request)


_origens = [o.strip() for o in os.getenv("ORIGENS_PERMITIDAS", "").split(",") if o.strip()]
if _origens:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origens,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth.router)
app.include_router(vagas.router)
app.include_router(candidatos.router)
app.include_router(ciclos.router)
app.include_router(gestores.router)
app.include_router(auditoria.router)
app.include_router(anotacoes.router)
app.include_router(canais.router)
app.include_router(listas.router)
app.include_router(exportar.router)
app.include_router(campos.router)
app.include_router(mensagens.router)
app.include_router(requisicoes.router)
app.include_router(acessos.router)
app.include_router(tempo_real.router)
app.include_router(busca.router)
app.include_router(painel.router)
app.include_router(fila.router)


@app.get("/status", tags=["Status"])
def status():
    return {"servico": "ATS TLM", "status": "ok", "docs": "/docs"}


_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@app.get("/", include_in_schema=False)
def front():
    return FileResponse(os.path.join(_STATIC_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")
