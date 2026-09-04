"""
Canal de tempo real.

O navegador abre uma conexao com /eventos e o servidor empurra um aviso
sempre que algo muda. Se a conexao cair (rede oscilando, notebook dormindo),
o navegador reconecta sozinho e informa o ultimo aviso que recebeu — assim
nada se perde no meio do caminho.
"""
import asyncio
import json

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse

from ..database import SessionLocal
from ..deps import get_current_user, usuario_do_token
from .. import eventos, models

router = APIRouter(tags=["Tempo real"])

INTERVALO = 1.5
BATIDA = 20.0


@router.get("/eventos/agora")
def agora(_: models.Usuario = Depends(get_current_user)):
    """Ponto de partida: o numero do ultimo aviso registrado."""
    db = SessionLocal()
    try:
        return {"ultimo": eventos.ultimo_id(db)}
    finally:
        db.close()


@router.get("/eventos")
async def canal(request: Request, desde: int = Query(0), token: str | None = Query(None)):
    """
    Mantem a conexao aberta e empurra as mudancas conforme elas acontecem.

    Formato SSE (padrao do navegador, funciona atras de HTTPS e proxy).
    """
    db_auth = SessionLocal()
    try:
        usuario_do_token(token, db_auth)
    finally:
        db_auth.close()

    async def fluxo():
        ultimo = desde
        db = SessionLocal()
        try:
            if ultimo <= 0:
                ultimo = eventos.ultimo_id(db)
                yield f"event: pronto\ndata: {json.dumps({'ultimo': ultimo})}\n\n"

            sem_novidade = 0.0
            while True:
                if await request.is_disconnected():
                    break
                try:
                    novas = await asyncio.to_thread(eventos.desde, db, ultimo)
                except Exception:
                    db.rollback()
                    novas = []
                if novas:
                    ultimo = novas[-1]["id"]
                    yield ("event: mudanca\n"
                           f"data: {json.dumps({'ultimo': ultimo, 'itens': novas})}\n\n")
                    sem_novidade = 0.0
                else:
                    sem_novidade += INTERVALO
                    if sem_novidade >= BATIDA:
                        yield ": batida\n\n"
                        sem_novidade = 0.0
                db.expire_all()
                await asyncio.sleep(INTERVALO)
        finally:
            db.close()

    return StreamingResponse(
        fluxo(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
