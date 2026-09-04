"""
Requisição de vaga: o gestor pede, a diretoria (ou o RH) aprova,
e a vaga é aberta automaticamente a partir do pedido aprovado.
"""
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import require_perm, get_current_user
from ..audit import registrar
from .. import models, schemas

router = APIRouter(prefix="/requisicoes", tags=["Requisições"])


@router.get("", response_model=list[schemas.RequisicaoOut])
def listar(status: str | None = Query(None), db: Session = Depends(get_db),
           _: models.Usuario = Depends(get_current_user)):
    stmt = select(models.Requisicao).order_by(models.Requisicao.id.desc())
    if status:
        stmt = stmt.where(models.Requisicao.status == status.upper())
    return db.scalars(stmt).all()


@router.post("", response_model=schemas.RequisicaoOut, status_code=201)
def criar(dados: schemas.RequisicaoIn, db: Session = Depends(get_db),
          ator: models.Usuario = Depends(require_perm("requisicoes.criar"))):
    req = models.Requisicao(**dados.model_dump(), solicitante=ator.nome, status="PENDENTE")
    db.add(req); db.flush()
    registrar(db, ator, "criar_requisicao", "requisicao", req.id,
              {"cargo": req.cargo, "qtde": req.qtde})
    db.commit(); db.refresh(req)
    return req


@router.patch("/{req_id}", response_model=schemas.RequisicaoOut)
def editar(req_id: int, dados: schemas.RequisicaoIn, db: Session = Depends(get_db),
           ator: models.Usuario = Depends(require_perm("requisicoes.criar"))):
    req = db.get(models.Requisicao, req_id)
    if not req:
        raise HTTPException(404, "Requisição não encontrada")
    if req.status != "PENDENTE":
        raise HTTPException(400, "Só é possível editar requisições pendentes.")
    for k, v in dados.model_dump(exclude_unset=True).items():
        setattr(req, k, v)
    registrar(db, ator, "editar_requisicao", "requisicao", req.id, {"cargo": req.cargo})
    db.commit(); db.refresh(req)
    return req


@router.post("/{req_id}/decidir", response_model=schemas.RequisicaoOut)
def decidir(req_id: int, dados: schemas.RequisicaoDecisao, db: Session = Depends(get_db),
            ator: models.Usuario = Depends(require_perm("requisicoes.aprovar"))):
    """Aprova (abrindo a vaga) ou recusa a requisição."""
    req = db.get(models.Requisicao, req_id)
    if not req:
        raise HTTPException(404, "Requisição não encontrada")
    if req.status != "PENDENTE":
        raise HTTPException(400, f"Esta requisição já foi {req.status.lower()}.")

    req.decidido_por = ator.nome
    req.decidido_em = datetime.now()
    req.observacao_decisao = dados.observacao_decisao

    if not dados.aprovar:
        req.status = "RECUSADA"
        registrar(db, ator, "recusar_requisicao", "requisicao", req.id, {"cargo": req.cargo})
        db.commit(); db.refresh(req)
        return req

    codigos = [v.codigo for v in db.scalars(select(models.Vaga)).all() if v.codigo]
    numeros = [int(c[1:]) for c in codigos if len(c) > 1 and c[0].upper() == "V" and c[1:].isdigit()]
    novo_codigo = f"V{(max(numeros) + 1) if numeros else 1:03d}"

    vaga = models.Vaga(
        codigo=novo_codigo, cargo=req.cargo, cargo_padrao=req.cargo, nivel=req.nivel,
        qtde=req.qtde or 1, tipo=req.tipo, motivo=req.motivo, salario=req.salario,
        area=req.area, linha=req.linha, gestor_id=req.gestor_id, status="ABERTURA",
        data_abertura=date.today(), previsao_inicio=req.previsao_inicio,
        observacoes=(f"Aberta pela requisição #{req.id}" +
                     (f" — substituindo {req.substituindo}" if req.substituindo else "")),
    )
    db.add(vaga); db.flush()
    req.status = "APROVADA"
    req.vaga_id = vaga.id
    registrar(db, ator, "aprovar_requisicao", "requisicao", req.id,
              {"cargo": req.cargo, "vaga": novo_codigo})
    db.commit(); db.refresh(req)
    return req


@router.delete("/{req_id}", status_code=204)
def excluir(req_id: int, db: Session = Depends(get_db),
            ator: models.Usuario = Depends(require_perm("requisicoes.aprovar"))):
    req = db.get(models.Requisicao, req_id)
    if not req:
        raise HTTPException(404, "Requisição não encontrada")
    if req.status == "APROVADA":
        raise HTTPException(400, "Requisição já aprovada não pode ser excluída (a vaga existe).")
    registrar(db, ator, "excluir_requisicao", "requisicao", req.id, {"cargo": req.cargo})
    db.delete(req); db.commit()
