"""Listas configuráveis — substitui a aba LISTAS da planilha."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import require_perm, get_current_user
from ..audit import registrar
from ..listas_padrao import ROTULOS, SENSIVEIS
from .. import models, schemas

router = APIRouter(prefix="/listas", tags=["Configurações"])


@router.get("", response_model=dict)
def listar(db: Session = Depends(get_db),
           _: models.Usuario = Depends(get_current_user)):
    """Devolve todas as listas agrupadas por tipo (só os valores ativos, em ordem)."""
    itens = db.scalars(select(models.Lista).order_by(models.Lista.tipo,
                                                     models.Lista.ordem,
                                                     models.Lista.valor)).all()
    agrupado: dict[str, list[str]] = {}
    for i in itens:
        if i.ativo:
            agrupado.setdefault(i.tipo, []).append(i.valor)
    return {"listas": agrupado, "rotulos": ROTULOS, "sensiveis": sorted(SENSIVEIS)}


@router.get("/todos", response_model=list[schemas.ListaOut])
def listar_todos(db: Session = Depends(get_db),
                 _: models.Usuario = Depends(require_perm("listas.gerenciar"))):
    """Lista completa (inclui inativos) para a tela de configurações."""
    return db.scalars(select(models.Lista).order_by(models.Lista.tipo,
                                                    models.Lista.ordem,
                                                    models.Lista.valor)).all()


@router.post("", response_model=schemas.ListaOut, status_code=201)
def criar(dados: schemas.ListaCreate, db: Session = Depends(get_db),
          ator: models.Usuario = Depends(require_perm("listas.gerenciar"))):
    existe = db.scalar(select(models.Lista).where(models.Lista.tipo == dados.tipo,
                                                  models.Lista.valor == dados.valor))
    if existe:
        raise HTTPException(400, "Esse valor já existe nesta lista")
    item = models.Lista(**dados.model_dump())
    db.add(item); db.flush()
    registrar(db, ator, "criar_item_lista", "lista", item.id, {"tipo": item.tipo, "valor": item.valor})
    db.commit(); db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=schemas.ListaOut)
def atualizar(item_id: int, dados: schemas.ListaUpdate, db: Session = Depends(get_db),
              ator: models.Usuario = Depends(require_perm("listas.gerenciar"))):
    item = db.get(models.Lista, item_id)
    if not item:
        raise HTTPException(404, "Item não encontrado")
    campos = dados.model_dump(exclude_unset=True)
    antigo = item.valor
    for k, v in campos.items():
        setattr(item, k, v)
    novo = campos.get("valor")
    if novo and novo != antigo:
        col = {"etapa": (models.Candidato, "etapa_atual"),
               "status_candidato": (models.Candidato, "status"),
               "origem": (models.Candidato, "origem"),
               "linha": (models.Candidato, "linha"),
               "status_vaga": (models.Vaga, "status"),
               "area": (models.Vaga, "area"),
               "nivel": (models.Vaga, "nivel"),
               "motivo": (models.Vaga, "motivo"),
               "tipo_contrato": (models.Vaga, "tipo"),
               "cargo": (models.Vaga, "cargo_padrao")}.get(item.tipo)
        if col:
            modelo, campo = col
            db.query(modelo).filter(getattr(modelo, campo) == antigo).update({campo: novo})
    registrar(db, ator, "editar_item_lista", "lista", item.id,
              {"tipo": item.tipo, "de": antigo, "para": item.valor})
    db.commit(); db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def excluir(item_id: int, db: Session = Depends(get_db),
            ator: models.Usuario = Depends(require_perm("listas.gerenciar"))):
    item = db.get(models.Lista, item_id)
    if not item:
        raise HTTPException(404, "Item não encontrado")
    registrar(db, ator, "excluir_item_lista", "lista", item.id,
              {"tipo": item.tipo, "valor": item.valor})
    db.delete(item); db.commit()


@router.get("/mapa-gestores", response_model=list[schemas.MapaOut])
def listar_mapa(db: Session = Depends(get_db),
                _: models.Usuario = Depends(get_current_user)):
    return db.scalars(select(models.MapaCargoGestor).order_by(models.MapaCargoGestor.cargo)).all()


@router.post("/mapa-gestores", response_model=schemas.MapaOut, status_code=201)
def salvar_mapa(dados: schemas.MapaCreate, db: Session = Depends(get_db),
                ator: models.Usuario = Depends(require_perm("listas.gerenciar"))):
    item = db.scalar(select(models.MapaCargoGestor).where(models.MapaCargoGestor.cargo == dados.cargo))
    if item:
        item.gestor = dados.gestor
    else:
        item = models.MapaCargoGestor(**dados.model_dump())
        db.add(item)
    db.flush()
    registrar(db, ator, "mapear_cargo_gestor", "lista", item.id,
              {"cargo": item.cargo, "gestor": item.gestor})
    db.commit(); db.refresh(item)
    return item


@router.delete("/mapa-gestores/{item_id}", status_code=204)
def excluir_mapa(item_id: int, db: Session = Depends(get_db),
                 ator: models.Usuario = Depends(require_perm("listas.gerenciar"))):
    item = db.get(models.MapaCargoGestor, item_id)
    if not item:
        raise HTTPException(404, "Item não encontrado")
    registrar(db, ator, "excluir_mapa_gestor", "lista", item_id,
              {"cargo": item.cargo, "gestor": item.gestor})
    db.delete(item); db.commit()
