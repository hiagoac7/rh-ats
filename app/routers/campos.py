"""Campos personalizados — permite ampliar o sistema sem mexer no código."""
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import require_perm, get_current_user
from ..audit import registrar
from .. import models, schemas

router = APIRouter(prefix="/campos", tags=["Configurações"])

TIPOS = {"texto", "numero", "data", "lista", "sim_nao"}


@router.get("", response_model=list[schemas.CampoOut])
def listar(entidade: str | None = None, db: Session = Depends(get_db),
           _: models.Usuario = Depends(get_current_user)):
    stmt = select(models.CampoPersonalizado).order_by(models.CampoPersonalizado.entidade,
                                                      models.CampoPersonalizado.ordem)
    if entidade:
        stmt = stmt.where(models.CampoPersonalizado.entidade == entidade)
    return db.scalars(stmt).all()


@router.post("", response_model=schemas.CampoOut, status_code=201)
def criar(dados: schemas.CampoCreate, db: Session = Depends(get_db),
          ator: models.Usuario = Depends(require_perm("listas.gerenciar"))):
    if dados.entidade not in {"candidato", "vaga"}:
        raise HTTPException(400, "Entidade deve ser 'candidato' ou 'vaga'")
    if dados.tipo not in TIPOS:
        raise HTTPException(400, f"Tipo deve ser um de: {', '.join(sorted(TIPOS))}")
    chave = re.sub(r"[^a-z0-9_]", "", dados.chave.strip().lower().replace(" ", "_"))
    if not chave:
        raise HTTPException(400, "Nome do campo inválido")
    existe = db.scalar(select(models.CampoPersonalizado).where(
        models.CampoPersonalizado.entidade == dados.entidade,
        models.CampoPersonalizado.chave == chave))
    if existe:
        raise HTTPException(400, "Já existe um campo com esse nome")
    campo = models.CampoPersonalizado(**{**dados.model_dump(), "chave": chave})
    db.add(campo); db.flush()
    registrar(db, ator, "criar_campo", "campo", campo.id,
              {"entidade": campo.entidade, "rotulo": campo.rotulo, "tipo": campo.tipo})
    db.commit(); db.refresh(campo)
    return campo


@router.patch("/{campo_id}", response_model=schemas.CampoOut)
def atualizar(campo_id: int, dados: schemas.CampoUpdate, db: Session = Depends(get_db),
              ator: models.Usuario = Depends(require_perm("listas.gerenciar"))):
    campo = db.get(models.CampoPersonalizado, campo_id)
    if not campo:
        raise HTTPException(404, "Campo não encontrado")
    campos = dados.model_dump(exclude_unset=True)
    if campos.get("tipo") and campos["tipo"] not in TIPOS:
        raise HTTPException(400, "Tipo inválido")
    for k, v in campos.items():
        setattr(campo, k, v)
    registrar(db, ator, "editar_campo", "campo", campo.id, campos)
    db.commit(); db.refresh(campo)
    return campo


@router.delete("/{campo_id}", status_code=204)
def excluir(campo_id: int, db: Session = Depends(get_db),
            ator: models.Usuario = Depends(require_perm("listas.gerenciar"))):
    campo = db.get(models.CampoPersonalizado, campo_id)
    if not campo:
        raise HTTPException(404, "Campo não encontrado")
    registrar(db, ator, "excluir_campo", "campo", campo.id, {"rotulo": campo.rotulo})
    db.delete(campo); db.commit()
