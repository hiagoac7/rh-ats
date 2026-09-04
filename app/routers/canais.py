"""
Canais de divulgação e candidaturas recebidas por canal.

Nota de segurança: NÃO armazenamos senhas de plataformas de vagas.
O campo `login` guarda apenas o usuário/e-mail usado, para referência.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import require_perm
from ..audit import registrar
from .. import models, schemas

router = APIRouter(tags=["Divulgação"])


@router.get("/canais", response_model=list[schemas.CanalOut])
def listar_canais(db: Session = Depends(get_db),
                  _: models.Usuario = Depends(require_perm("vagas.ver"))):
    return db.scalars(select(models.Canal).order_by(models.Canal.nome)).all()


@router.post("/canais", response_model=schemas.CanalOut, status_code=201)
def criar_canal(dados: schemas.CanalCreate, db: Session = Depends(get_db),
                ator: models.Usuario = Depends(require_perm("canais.gerenciar"))):
    if db.scalar(select(models.Canal).where(models.Canal.nome == dados.nome)):
        raise HTTPException(400, "Já existe um canal com esse nome")
    c = models.Canal(**dados.model_dump())
    db.add(c); db.flush()
    registrar(db, ator, "criar_canal", "canal", c.id, {"nome": c.nome})
    db.commit(); db.refresh(c)
    return c


@router.patch("/canais/{canal_id}", response_model=schemas.CanalOut)
def atualizar_canal(canal_id: int, dados: schemas.CanalUpdate, db: Session = Depends(get_db),
                    ator: models.Usuario = Depends(require_perm("canais.gerenciar"))):
    c = db.get(models.Canal, canal_id)
    if not c:
        raise HTTPException(404, "Canal não encontrado")
    campos = dados.model_dump(exclude_unset=True)
    for k, v in campos.items():
        setattr(c, k, v)
    registrar(db, ator, "editar_canal", "canal", c.id, campos)
    db.commit(); db.refresh(c)
    return c


@router.delete("/canais/{canal_id}", status_code=204)
def excluir_canal(canal_id: int, db: Session = Depends(get_db),
                  ator: models.Usuario = Depends(require_perm("canais.gerenciar"))):
    c = db.get(models.Canal, canal_id)
    if not c:
        raise HTTPException(404, "Canal não encontrado")
    db.query(models.Candidatura).filter_by(canal_id=canal_id).delete()
    registrar(db, ator, "excluir_canal", "canal", c.id, {"nome": c.nome})
    db.delete(c); db.commit()


@router.get("/candidaturas", response_model=list[schemas.CandidaturaOut])
def listar_candidaturas(vaga_id: int | None = Query(None), canal_id: int | None = Query(None),
                        db: Session = Depends(get_db),
                        _: models.Usuario = Depends(require_perm("vagas.ver"))):
    stmt = select(models.Candidatura).order_by(models.Candidatura.id.desc())
    if vaga_id:
        stmt = stmt.where(models.Candidatura.vaga_id == vaga_id)
    if canal_id:
        stmt = stmt.where(models.Candidatura.canal_id == canal_id)
    return db.scalars(stmt).all()


@router.post("/candidaturas", response_model=schemas.CandidaturaOut, status_code=201)
def registrar_candidaturas(dados: schemas.CandidaturaCreate, db: Session = Depends(get_db),
                           ator: models.Usuario = Depends(require_perm("canais.gerenciar"))):
    if not db.get(models.Canal, dados.canal_id):
        raise HTTPException(404, "Canal não encontrado")
    c = models.Candidatura(**dados.model_dump())
    db.add(c); db.flush()
    registrar(db, ator, "registrar_candidaturas", "canal", dados.canal_id,
              {"quantidade": dados.quantidade, "vaga_id": dados.vaga_id})
    db.commit(); db.refresh(c)
    return c


@router.delete("/candidaturas/{cid}", status_code=204)
def excluir_candidatura(cid: int, db: Session = Depends(get_db),
                        ator: models.Usuario = Depends(require_perm("canais.gerenciar"))):
    c = db.get(models.Candidatura, cid)
    if not c:
        raise HTTPException(404, "Registro não encontrado")
    registrar(db, ator, "excluir_candidatura", "candidatura", cid,
              {"canal_id": c.canal_id, "vaga_id": c.vaga_id})
    db.delete(c); db.commit()
