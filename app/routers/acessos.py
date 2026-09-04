"""
Acessos de TI para novos contratados.

Quando um candidato e aprovado, o sistema abre automaticamente um pedido
de acessos para o TI (e-mail, rede, ERP, equipamento...). Esta rota mostra
a fila desses pedidos e permite dar baixa item a item.
"""
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import require_perm
from ..audit import registrar
from .. import models, schemas

router = APIRouter(prefix="/acessos", tags=["Acessos TI"])


def _montar(db: Session, a: models.AcessoTI) -> schemas.AcessoOut:
    c = db.get(models.Candidato, a.candidato_id)
    vaga = db.get(models.Vaga, c.vaga_id) if (c and c.vaga_id) else None
    saida = schemas.AcessoOut.model_validate(a)
    if c:
        saida.candidato = c.nome
        saida.cargo = (vaga.cargo_padrao or vaga.cargo) if vaga else c.cargo
        saida.gestor = c.gestor_nome
        saida.email = c.email
        saida.contato = c.contato
        saida.data_aprovacao = c.data_aprovacao
    if vaga:
        saida.area = vaga.area
        saida.previsao_inicio = vaga.previsao_inicio
    return saida


@router.get("", response_model=list[schemas.AcessoOut])
def listar(status: str | None = Query(None), db: Session = Depends(get_db),
           _: models.Usuario = Depends(require_perm("acessos.ver"))):
    stmt = select(models.AcessoTI).order_by(models.AcessoTI.id.desc())
    if status:
        stmt = stmt.where(models.AcessoTI.status == status.upper())
    itens = db.scalars(stmt).all()
    validos = []
    orfaos = False
    for a in itens:
        if db.get(models.Candidato, a.candidato_id) is None:
            db.delete(a); orfaos = True
        else:
            validos.append(a)
    if orfaos:
        db.commit()
    return [_montar(db, a) for a in validos]


@router.get("/pendentes")
def contar_pendentes(db: Session = Depends(get_db),
                     _: models.Usuario = Depends(require_perm("acessos.ver"))):
    n = db.query(models.AcessoTI).filter(models.AcessoTI.status != "CONCLUIDO").count()
    return {"pendentes": n}


@router.patch("/{acesso_id}", response_model=schemas.AcessoOut)
def atualizar(acesso_id: int, dados: schemas.AcessoUpdate, db: Session = Depends(get_db),
              ator: models.Usuario = Depends(require_perm("acessos.gerenciar"))):
    a = db.get(models.AcessoTI, acesso_id)
    if not a:
        raise HTTPException(404, "Pedido de acesso não encontrado")
    campos = dados.model_dump(exclude_unset=True)
    if "itens" in campos and campos["itens"] is not None:
        a.itens = campos["itens"]
        if a.itens and all(a.itens.values()) and a.status != "CONCLUIDO":
            campos.setdefault("status", "CONCLUIDO")
        elif a.status == "PENDENTE" and any(a.itens.values()):
            campos.setdefault("status", "EM ANDAMENTO")
    if campos.get("status"):
        a.status = campos["status"].upper()
        if a.status == "CONCLUIDO":
            a.concluido_em = datetime.now()
            a.responsavel = ator.nome
        else:
            a.concluido_em = None
    if "observacoes" in campos:
        a.observacoes = campos["observacoes"]
    registrar(db, ator, "atualizar_acessos", "acesso", a.id,
              {"status": a.status, "candidato_id": a.candidato_id})
    db.commit(); db.refresh(a)
    return _montar(db, a)


@router.post("/{acesso_id}/reabrir", response_model=schemas.AcessoOut)
def reabrir(acesso_id: int, db: Session = Depends(get_db),
            ator: models.Usuario = Depends(require_perm("acessos.gerenciar"))):
    a = db.get(models.AcessoTI, acesso_id)
    if not a:
        raise HTTPException(404, "Pedido não encontrado")
    a.status = "EM ANDAMENTO"; a.concluido_em = None
    registrar(db, ator, "reabrir_acessos", "acesso", a.id, {})
    db.commit(); db.refresh(a)
    return _montar(db, a)


def sincronizar_aprovados(db: Session, dias_para_tras: int = 0) -> dict:
    """
    Cria os pedidos de acesso que faltam para candidatos ja aprovados.

    Regra:
      - inicio hoje ou no futuro           -> PENDENTE (o TI precisa agir)
      - inicio no passado                  -> CONCLUIDO (ja esta trabalhando)
      - sem data e aprovado ha ate 30 dias -> PENDENTE
      - sem data e aprovado ha mais tempo  -> CONCLUIDO
    """
    hoje = date.today()
    corte = hoje - timedelta(days=dias_para_tras)
    itens_padrao = {l.valor: False for l in db.query(models.Lista)
                    .filter_by(tipo="acesso_ti", ativo=True)
                    .order_by(models.Lista.ordem).all()}
    ja_tem = {a.candidato_id for a in db.query(models.AcessoTI).all()}
    criados = {"pendentes": 0, "historicos": 0}

    aprovados = db.scalars(select(models.Candidato)).all()
    vagas = {v.id: v for v in db.scalars(select(models.Vaga)).all()}
    for c in aprovados:
        if (c.status or "").strip().upper() != "APROVADO" or c.id in ja_tem:
            continue
        vaga = vagas.get(c.vaga_id) if c.vaga_id else None
        inicio = vaga.previsao_inicio if vaga else None
        if inicio is not None:
            pendente = inicio >= corte
        else:
            pendente = (c.data_aprovacao is None) or ((hoje - c.data_aprovacao).days <= 30)
        db.add(models.AcessoTI(
            candidato_id=c.id,
            status="PENDENTE" if pendente else "CONCLUIDO",
            itens=dict(itens_padrao) if pendente else {k: True for k in itens_padrao},
            observacoes=None if pendente else "Contratação anterior ao sistema — marcada como concluída.",
            concluido_em=None if pendente else datetime.now(),
            responsavel=None if pendente else "sistema",
        ))
        criados["pendentes" if pendente else "historicos"] += 1
    db.commit()
    return criados


@router.post("/sincronizar")
def sincronizar(db: Session = Depends(get_db),
                ator: models.Usuario = Depends(require_perm("acessos.gerenciar"))):
    """Procura aprovados que ainda nao tem pedido de acesso e cria."""
    r = sincronizar_aprovados(db)
    registrar(db, ator, "sincronizar_acessos", "acesso", None, r)
    db.commit()
    return r
