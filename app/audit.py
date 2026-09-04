"""Registro de auditoria — grava quem fez o quê e quando."""
from sqlalchemy.orm import Session
from . import models
from .eventos import marcar_ator

SENSIVEIS = {"senha", "senha_hash", "password"}


def registrar(db: Session, ator, acao: str, entidade: str | None = None,
              entidade_id=None, detalhes: dict | None = None) -> None:
    """Cria uma entrada de auditoria. NÃO faz commit (o chamador comita)."""
    d = None
    if detalhes:
        d = {k: (v.isoformat() if hasattr(v, "isoformat") else v)
             for k, v in detalhes.items() if k not in SENSIVEIS}
    marcar_ator(db, getattr(ator, "nome", None))
    db.add(models.Auditoria(
        ator_id=getattr(ator, "id", None),
        ator_nome=getattr(ator, "nome", None) or getattr(ator, "email", None),
        acao=acao,
        entidade=entidade,
        entidade_id=str(entidade_id) if entidade_id is not None else None,
        detalhes=d,
    ))
