"""Busca geral: encontra candidato, vaga ou gestor de qualquer tela."""
import re
import unicodedata

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from .. import models

router = APIRouter(tags=["Busca"])


def _limpo(t: str | None) -> str:
    """Sem acento e em minusculas, para achar 'Suenia' digitando 'suenia'."""
    if not t:
        return ""
    s = unicodedata.normalize("NFKD", str(t))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def _digitos(t: str | None) -> str:
    return re.sub(r"\D", "", t or "")


@router.get("/busca")
def buscar(q: str = Query("", min_length=0), limite: int = Query(8),
           db: Session = Depends(get_db),
           user: models.Usuario = Depends(get_current_user)):
    """
    Procura em candidatos, vagas e gestores ao mesmo tempo.

    Encontra por nome, cargo, codigo da vaga, e-mail, telefone e CPF.
    So devolve o que o usuario tem permissao de ver.
    """
    termo = _limpo(q).strip()
    if len(termo) < 2:
        return {"candidatos": [], "vagas": [], "gestores": []}
    num = _digitos(q)
    perms = set(user.permissoes)
    saida = {"candidatos": [], "vagas": [], "gestores": []}

    if "candidatos.ver" in perms:
        for c in db.scalars(select(models.Candidato)).all():
            achou = (termo in _limpo(c.nome) or termo in _limpo(c.cargo)
                     or termo in _limpo(c.email)
                     or (len(num) >= 4 and (num in _digitos(c.contato) or num in _digitos(c.cpf))))
            if achou:
                saida["candidatos"].append({
                    "id": c.id, "nome": c.nome, "cargo": c.cargo,
                    "status": c.status, "etapa": c.etapa_atual,
                    "contato": c.contato, "email": c.email})
                if len(saida["candidatos"]) >= limite:
                    break

    if "vagas.ver" in perms:
        for v in db.scalars(select(models.Vaga)).all():
            if (termo in _limpo(v.cargo) or termo in _limpo(v.cargo_padrao)
                    or termo in _limpo(v.codigo) or termo in _limpo(v.area)):
                saida["vagas"].append({
                    "id": v.id, "codigo": v.codigo,
                    "cargo": v.cargo_padrao or v.cargo,
                    "status": v.status, "area": v.area})
                if len(saida["vagas"]) >= limite:
                    break

    if "vagas.ver" in perms:
        for g in db.scalars(select(models.Gestor)).all():
            if termo in _limpo(g.nome):
                saida["gestores"].append({"id": g.id, "nome": g.nome, "email": g.email})
                if len(saida["gestores"]) >= 5:
                    break

    return saida
