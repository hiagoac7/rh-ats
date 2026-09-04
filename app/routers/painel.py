"""Indicadores calculados (equivale a aba PAINEL da planilha)."""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import require_perm
from .. import models, schemas

router = APIRouter(tags=["Painel"], dependencies=[Depends(require_perm("painel.ver"))])

STATUS_FINAIS = {"APROVADO", "REPROVADO", "DECLINOU", "DESISTIU", "SEM RETORNO", "CANCELADO"}


@router.get("/painel", response_model=schemas.PainelOut)
def painel(db: Session = Depends(get_db)):
    cands = db.scalars(select(models.Candidato)).all()

    cadastrados = len(cands)
    aprovados = sum(1 for c in cands if (c.status or "").upper() == "APROVADO")
    em_processo = sum(1 for c in cands if (c.status or "").upper() not in STATUS_FINAIS)
    taxa = round(aprovados / cadastrados, 4) if cadastrados else 0.0

    vagas_abertas = db.scalar(
        select(func.count()).select_from(models.Vaga).where(models.Vaga.status != "FECHADA")
    ) or 0

    funil: dict[str, int] = {}
    for c in cands:
        etapa = c.etapa_atual or "Sem etapa"
        funil[etapa] = funil.get(etapa, 0) + 1

    return schemas.PainelOut(
        candidatos_cadastrados=cadastrados,
        em_processo=em_processo,
        aprovados=aprovados,
        taxa_aprovacao=taxa,
        vagas_em_aberto=vagas_abertas,
        funil=dict(sorted(funil.items())),
    )


@router.get("/avaliacoes")
def resumo_avaliacoes(db: Session = Depends(get_db),
                      _: models.Usuario = Depends(require_perm("painel.ver"))):
    """
    Quem avalia como.

    Serve para uma conversa dificil de ter sem dado: se um avaliador recomenda
    contratar em 90% dos casos e outro em 20%, a nota deles nao significa a
    mesma coisa — e a decisao precisa levar isso em conta.
    """
    todas = db.scalars(select(models.Avaliacao)).all()
    if not todas:
        return {"total": 0, "por_avaliador": [], "por_criterio": []}

    por_autor: dict[str, dict] = {}
    soma_criterio: dict[str, list] = {}
    for a in todas:
        nome = a.autor or "—"
        d = por_autor.setdefault(nome, {"avaliador": nome, "avaliacoes": 0,
                                        "recomendou": 0, "notas": []})
        d["avaliacoes"] += 1
        if (a.recomendacao or "") == "Sim":
            d["recomendou"] += 1
        if a.media is not None:
            d["notas"].append(a.media)
        for criterio, nota in (a.notas or {}).items():
            if isinstance(nota, (int, float)):
                soma_criterio.setdefault(criterio, []).append(nota)

    por_avaliador = []
    for d in por_autor.values():
        notas = d.pop("notas")
        d["media"] = round(sum(notas) / len(notas), 1) if notas else None
        d["taxa_recomendacao"] = round(d["recomendou"] / d["avaliacoes"], 2)
        por_avaliador.append(d)
    por_avaliador.sort(key=lambda x: -x["avaliacoes"])

    por_criterio = sorted(
        ({"criterio": k, "media": round(sum(v) / len(v), 1), "avaliacoes": len(v)}
         for k, v in soma_criterio.items()),
        key=lambda x: x["media"])

    return {"total": len(todas), "por_avaliador": por_avaliador, "por_criterio": por_criterio}
