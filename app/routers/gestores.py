from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import require_perm
from .. import models, schemas
from ..audit import registrar

router = APIRouter(prefix="/gestores", tags=["Gestores"],
                   dependencies=[Depends(require_perm("vagas.ver"))])


@router.get("", response_model=list[schemas.GestorOut])
def listar(db: Session = Depends(get_db)):
    return db.scalars(select(models.Gestor).order_by(models.Gestor.nome)).all()


@router.post("", response_model=schemas.GestorOut, status_code=201)
def criar(dados: schemas.GestorCreate, db: Session = Depends(get_db),
          _: models.Usuario = Depends(require_perm("gestores.gerenciar"))):
    existe = db.scalar(select(models.Gestor).where(models.Gestor.nome == dados.nome))
    if existe:
        return existe
    g = models.Gestor(**dados.model_dump())
    db.add(g); db.commit(); db.refresh(g)
    return g


@router.patch("/{gestor_id}", response_model=schemas.GestorOut)
def atualizar(gestor_id: int, dados: schemas.GestorUpdate, db: Session = Depends(get_db),
              ator: models.Usuario = Depends(require_perm("gestores.gerenciar"))):
    g = db.get(models.Gestor, gestor_id)
    if not g:
        raise HTTPException(404, "Gestor não encontrado")
    campos = dados.model_dump(exclude_unset=True)
    for k, v in campos.items():
        setattr(g, k, v)
    registrar(db, ator, "editar_gestor", "gestor", g.id, campos)
    db.commit(); db.refresh(g)
    return g


@router.delete("/{gestor_id}", status_code=204)
def excluir(gestor_id: int, db: Session = Depends(get_db),
            ator: models.Usuario = Depends(require_perm("gestores.gerenciar"))):
    g = db.get(models.Gestor, gestor_id)
    if not g:
        raise HTTPException(404, "Gestor não encontrado")
    em_uso = db.scalar(select(models.Vaga).where(models.Vaga.gestor_id == gestor_id))
    if em_uso:
        raise HTTPException(400, "Este gestor tem vagas vinculadas. Reatribua as vagas antes de excluir.")
    db.query(models.Requisicao).filter_by(gestor_id=gestor_id).update({"gestor_id": None})
    db.query(models.MapaCargoGestor).filter_by(gestor=g.nome).delete()
    registrar(db, ator, "excluir_gestor", "gestor", g.id, {"nome": g.nome})
    db.delete(g); db.commit()
