from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import require_perm
from .. import models, schemas
from ..audit import registrar
from .. import validacoes, duplicidade

router = APIRouter(prefix="/vagas", tags=["Vagas"])


@router.get("", response_model=list[schemas.VagaOut])
def listar_vagas(status: str | None = Query(None), gestor_id: int | None = None,
                 db: Session = Depends(get_db),
                 _: models.Usuario = Depends(require_perm("vagas.ver"))):
    stmt = select(models.Vaga)
    if status:
        stmt = stmt.where(models.Vaga.status == status)
    if gestor_id:
        stmt = stmt.where(models.Vaga.gestor_id == gestor_id)
    return db.scalars(stmt).all()


@router.get("/{vaga_id}", response_model=schemas.VagaOut)
def obter_vaga(vaga_id: int, db: Session = Depends(get_db),
               _: models.Usuario = Depends(require_perm("vagas.ver"))):
    vaga = db.get(models.Vaga, vaga_id)
    if not vaga:
        raise HTTPException(404, "Vaga não encontrada")
    return vaga


@router.post("", response_model=schemas.VagaOut, status_code=201)
def criar_vaga(dados: schemas.VagaCreate, db: Session = Depends(get_db),
               ator: models.Usuario = Depends(require_perm("vagas.criar"))):
    campos = dados.model_dump()
    confirmou_dup = campos.pop("confirmar_duplicado", False)
    if not confirmou_dup:
        parecidas = duplicidade.vagas_parecidas(
            db, campos.get("codigo"), campos.get("cargo"), campos.get("cargo_padrao"))
        if parecidas:
            raise HTTPException(status_code=409, detail={
                "tipo": "duplicado",
                "mensagem": "Já existe vaga parecida no sistema.",
                "encontrados": parecidas})
    vaga = models.Vaga(**campos)
    db.add(vaga); db.flush()
    registrar(db, ator, "criar_vaga", "vaga", vaga.id, {"cargo": vaga.cargo, "codigo": vaga.codigo})
    db.commit(); db.refresh(vaga)
    return vaga


@router.patch("/{vaga_id}", response_model=schemas.VagaOut)
def atualizar_vaga(vaga_id: int, dados: schemas.VagaUpdate, db: Session = Depends(get_db),
                   ator: models.Usuario = Depends(require_perm("vagas.editar"))):
    vaga = db.get(models.Vaga, vaga_id)
    if not vaga:
        raise HTTPException(404, "Vaga não encontrada")
    campos = dados.model_dump(exclude_unset=True)
    confirmou = campos.pop("confirmar_pendencias", False)
    campos.pop("confirmar_duplicado", None)
    versao_tela = campos.pop("versao", None)

    if versao_tela is not None and versao_tela != (vaga.versao or 1):
        raise HTTPException(status_code=409, detail={
            "tipo": "conflito",
            "mensagem": (f"A vaga {vaga.codigo or vaga.cargo} foi alterada por outra pessoa "
                         "enquanto você editava. Recarregue antes de salvar."),
            "versao_atual": vaga.versao or 1})

    for campo, valor in campos.items():
        setattr(vaga, campo, valor)
    vaga.versao = (vaga.versao or 1) + 1

    fechando = (campos.get("status") or "").upper() == "FECHADA"
    if fechando and not confirmou:
        faltando = validacoes.importantes(validacoes.pendencias_vaga(db, vaga, fechando=True))
        if faltando:
            db.rollback()
            raise HTTPException(status_code=422, detail={
                "tipo": "pendencias",
                "mensagem": "Faltam informações importantes para fechar esta vaga.",
                "pendencias": faltando})
    if fechando and confirmou:
        pend = validacoes.importantes(validacoes.pendencias_vaga(db, vaga, fechando=True))
        if pend:
            registrar(db, ator, "fechar_vaga_com_pendencias", "vaga", vaga.id,
                      {"faltando": [p["rotulo"] for p in pend]})
    registrar(db, ator, "editar_vaga", "vaga", vaga.id, campos)
    db.commit(); db.refresh(vaga)
    return vaga


@router.post("/{vaga_id}/reabrir", response_model=schemas.VagaOut, status_code=201)
def reabrir_vaga(vaga_id: int, db: Session = Depends(get_db),
                 ator: models.Usuario = Depends(require_perm("vagas.reabrir", "vagas.criar"))):
    """
    Reabre uma vaga recorrente (Vendedor, SDR, BDR...).

    Cria uma NOVA vaga copiando cargo, nivel, tipo, salario, area, linha e gestor,
    com status ABERTURA e abertura hoje. Tambem registra um ciclo, para o
    historico de aberturas/fechamentos do cargo ficar rastreavel.
    """
    from datetime import date as _date
    origem = db.get(models.Vaga, vaga_id)
    if not origem:
        raise HTTPException(404, "Vaga não encontrada")

    codigos = [v.codigo for v in db.scalars(select(models.Vaga)).all() if v.codigo]
    numeros = [int(c[1:]) for c in codigos if len(c) > 1 and c[0].upper() == "V" and c[1:].isdigit()]
    novo_codigo = f"V{(max(numeros) + 1) if numeros else 1:03d}"

    nova = models.Vaga(
        codigo=novo_codigo,
        cargo=origem.cargo,
        cargo_padrao=origem.cargo_padrao or origem.cargo,
        nivel=origem.nivel,
        qtde=origem.qtde or 1,
        tipo=origem.tipo,
        salario=origem.salario,
        area=origem.area,
        linha=origem.linha,
        gestor_id=origem.gestor_id,
        status="ABERTURA",
        data_abertura=_date.today(),
        observacoes=f"Reaberta a partir de {origem.codigo or origem.cargo}",
    )
    db.add(nova); db.flush()

    db.add(models.CicloVaga(
        vaga_id=nova.id, linha=origem.linha, data_abertura=_date.today(),
        status="ABERTO", observacoes=f"Ciclo aberto a partir de {origem.codigo or origem.cargo}",
    ))
    registrar(db, ator, "reabrir_vaga", "vaga", nova.id,
              {"origem": origem.codigo, "novo_codigo": novo_codigo, "cargo": nova.cargo})
    db.commit(); db.refresh(nova)
    return nova


@router.delete("/{vaga_id}", status_code=204)
def excluir_vaga(vaga_id: int, db: Session = Depends(get_db),
                 ator: models.Usuario = Depends(require_perm("vagas.excluir"))):
    vaga = db.get(models.Vaga, vaga_id)
    if not vaga:
        raise HTTPException(404, "Vaga não encontrada")
    n = db.query(models.Candidato).filter_by(vaga_id=vaga_id).count()
    if n:
        raise HTTPException(400, f"Esta vaga tem {n} candidato(s) vinculado(s). "
                                 "Mova ou desvincule os candidatos antes de excluir.")
    db.query(models.CicloVaga).filter_by(vaga_id=vaga_id).delete()
    db.query(models.Candidatura).filter_by(vaga_id=vaga_id).update({"vaga_id": None})
    db.query(models.Requisicao).filter_by(vaga_id=vaga_id).update({"vaga_id": None})
    registrar(db, ator, "excluir_vaga", "vaga", vaga.id, {"codigo": vaga.codigo, "cargo": vaga.cargo})
    db.delete(vaga); db.commit()


@router.get("/{vaga_id}/pendencias", response_model=schemas.PendenciasResposta)
def pendencias(vaga_id: int, fechando: bool = False, db: Session = Depends(get_db),
               _: models.Usuario = Depends(require_perm("vagas.ver"))):
    """O que falta preencher nesta vaga."""
    vaga = db.get(models.Vaga, vaga_id)
    if not vaga:
        raise HTTPException(404, "Vaga não encontrada")
    lista = validacoes.pendencias_vaga(db, vaga, fechando=fechando)
    return schemas.PendenciasResposta(
        pendencias=lista, bloqueia=bool(validacoes.importantes(lista)) and fechando)
