from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import require_perm
from .. import models, schemas

router = APIRouter(prefix="/candidatos/{cand_id}/anotacoes", tags=["Anotações"])


@router.get("", response_model=list[schemas.AnotacaoOut])
def listar(cand_id: int, db: Session = Depends(get_db),
           _: models.Usuario = Depends(require_perm("candidatos.ver"))):
    return db.scalars(
        select(models.Anotacao).where(models.Anotacao.candidato_id == cand_id)
        .order_by(models.Anotacao.id.desc())
    ).all()


@router.post("", response_model=schemas.AnotacaoOut, status_code=201)
def criar(cand_id: int, dados: schemas.AnotacaoCreate, db: Session = Depends(get_db),
          ator: models.Usuario = Depends(require_perm("candidatos.anotar", "candidatos.editar", "candidatos.parecer"))):
    if not db.get(models.Candidato, cand_id):
        raise HTTPException(404, "Candidato não encontrado")
    a = models.Anotacao(candidato_id=cand_id, autor=ator.nome, texto=dados.texto)
    db.add(a); db.commit(); db.refresh(a)
    return a
