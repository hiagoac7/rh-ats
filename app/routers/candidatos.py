from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import require_perm
from .. import models, schemas, historico
from ..audit import registrar
from ..automacoes import aplicar as aplicar_automacoes
from .. import validacoes, duplicidade

router = APIRouter(prefix="/candidatos", tags=["Candidatos"])


@router.get("", response_model=list[schemas.CandidatoOut])
def listar_candidatos(vaga_id: int | None = None, status: str | None = None,
                      etapa: str | None = Query(None), db: Session = Depends(get_db),
                      _: models.Usuario = Depends(require_perm("candidatos.ver"))):
    stmt = select(models.Candidato)
    if vaga_id:
        stmt = stmt.where(models.Candidato.vaga_id == vaga_id)
    if status:
        stmt = stmt.where(models.Candidato.status == status)
    if etapa:
        stmt = stmt.where(models.Candidato.etapa_atual == etapa)
    return db.scalars(stmt).all()


@router.get("/{cand_id}", response_model=schemas.CandidatoOut)
def obter_candidato(cand_id: int, db: Session = Depends(get_db),
                    _: models.Usuario = Depends(require_perm("candidatos.ver"))):
    cand = db.get(models.Candidato, cand_id)
    if not cand:
        raise HTTPException(404, "Candidato não encontrado")
    return cand


@router.post("", response_model=schemas.CandidatoOut, status_code=201)
def criar_candidato(dados: schemas.CandidatoCreate, db: Session = Depends(get_db),
                    ator: models.Usuario = Depends(require_perm("candidatos.criar"))):
    campos = dados.model_dump()
    confirmou = campos.pop("confirmar_pendencias", False)
    confirmou_dup = campos.pop("confirmar_duplicado", False)
    enviados = set(dados.model_dump(exclude_unset=True)) - {"confirmar_pendencias", "confirmar_duplicado"}

    if not confirmou_dup:
        parecidos = duplicidade.candidatos_parecidos(
            db, campos.get("nome"), campos.get("cpf"), campos.get("email"), campos.get("contato"))
        if parecidos:
            raise HTTPException(status_code=409, detail={
                "tipo": "duplicado",
                "mensagem": "Já existe candidato com estes dados no sistema.",
                "encontrados": parecidos})

    cand = models.Candidato(**campos)

    if (cand.status or "").strip().upper() == "APROVADO" and not confirmou:
        faltando = validacoes.importantes(validacoes.pendencias_candidato(db, cand, aprovando=True))
        if faltando:
            raise HTTPException(status_code=422, detail={
                "tipo": "pendencias",
                "mensagem": "Faltam informações importantes para aprovar este candidato.",
                "pendencias": faltando})

    db.add(cand); db.flush()
    aplicar_automacoes(db, cand, enviados)
    registrar(db, ator, "criar_candidato", "candidato", cand.id, {"nome": cand.nome, "vaga_id": cand.vaga_id})
    db.commit(); db.refresh(cand)
    return cand


@router.patch("/{cand_id}", response_model=schemas.CandidatoOut)
def atualizar_candidato(cand_id: int, dados: schemas.CandidatoUpdate, db: Session = Depends(get_db),
                        ator: models.Usuario = Depends(require_perm("candidatos.editar", "candidatos.parecer"))):
    cand = db.get(models.Candidato, cand_id)
    if not cand:
        raise HTTPException(404, "Candidato não encontrado")
    campos = dados.model_dump(exclude_unset=True)
    confirmou = campos.pop("confirmar_pendencias", False)
    campos.pop("confirmar_duplicado", None)
    versao_tela = campos.pop("versao", None)

    if versao_tela is not None and versao_tela != (cand.versao or 1):
        raise HTTPException(status_code=409, detail={
            "tipo": "conflito",
            "mensagem": (f"{cand.nome} foi alterado por outra pessoa enquanto você editava. "
                         "Recarregue para ver a versão atual antes de salvar."),
            "versao_atual": cand.versao or 1})

    for campo, valor in campos.items():
        setattr(cand, campo, valor)
    cand.versao = (cand.versao or 1) + 1

    aprovando = (campos.get("status") or "").upper() == "APROVADO"
    if aprovando and not confirmou:
        faltando = validacoes.importantes(validacoes.pendencias_candidato(db, cand, aprovando=True))
        if faltando:
            db.rollback()
            raise HTTPException(status_code=422, detail={
                "tipo": "pendencias",
                "mensagem": "Faltam informações importantes para aprovar este candidato.",
                "pendencias": faltando})
    if aprovando and confirmou:
        pend = validacoes.importantes(validacoes.pendencias_candidato(db, cand, aprovando=True))
        if pend:
            registrar(db, ator, "aprovar_com_pendencias", "candidato", cand.id,
                      {"faltando": [p["rotulo"] for p in pend]})
    aplicar_automacoes(db, cand, set(campos))
    registrar(db, ator, "editar_candidato", "candidato", cand.id, campos)
    db.commit(); db.refresh(cand)
    return cand


@router.delete("/{cand_id}", status_code=204)
def excluir_candidato(cand_id: int, db: Session = Depends(get_db),
                      ator: models.Usuario = Depends(require_perm("candidatos.excluir"))):
    cand = db.get(models.Candidato, cand_id)
    if not cand:
        raise HTTPException(404, "Candidato não encontrado")
    db.query(models.Anotacao).filter_by(candidato_id=cand_id).delete()
    db.query(models.AcessoTI).filter_by(candidato_id=cand_id).delete()
    registrar(db, ator, "excluir_candidato", "candidato", cand.id,
              {"nome": cand.nome, "vaga_id": cand.vaga_id})
    db.delete(cand); db.commit()


@router.get("/{cand_id}/avaliacoes", response_model=list[schemas.AvaliacaoOut])
def listar_avaliacoes(cand_id: int, db: Session = Depends(get_db),
                      _: models.Usuario = Depends(require_perm("candidatos.ver"))):
    return db.scalars(
        select(models.Avaliacao)
        .where(models.Avaliacao.candidato_id == cand_id)
        .order_by(models.Avaliacao.id.desc())
    ).all()


@router.post("/{cand_id}/avaliacoes", response_model=schemas.AvaliacaoOut, status_code=201)
def criar_avaliacao(cand_id: int, dados: schemas.AvaliacaoCreate, db: Session = Depends(get_db),
                    ator: models.Usuario = Depends(
                        require_perm("candidatos.parecer", "candidatos.editar"))):
    """
    Registra a avaliacao de uma entrevista.

    Cada entrevistador guarda a sua: duas pessoas podem avaliar a mesma etapa
    sem sobrescrever uma a outra — e a divergencia entre elas e justamente o
    que interessa numa decisao de contratacao.
    """
    if not db.get(models.Candidato, cand_id):
        raise HTTPException(404, "Candidato não encontrado")
    notas = {k: v for k, v in (dados.notas or {}).items() if isinstance(v, int) and 1 <= v <= 5}
    if not notas and not (dados.comentario or "").strip():
        raise HTTPException(400, "Dê ao menos uma nota ou escreva um comentário.")
    a = models.Avaliacao(
        candidato_id=cand_id, etapa=(dados.etapa or "RH")[:30], autor=ator.nome,
        notas=notas, recomendacao=dados.recomendacao, comentario=dados.comentario)
    db.add(a)
    registrar(db, ator, "avaliou_entrevista", "candidato", cand_id,
              {"etapa": a.etapa, "recomendacao": a.recomendacao, "media": None})
    db.commit(); db.refresh(a)
    return a


@router.get("/{cand_id}/historico", response_model=list[schemas.EventoHistorico])
def historico_candidato(cand_id: int, db: Session = Depends(get_db),
                        _: models.Usuario = Depends(require_perm("candidatos.ver"))):
    """
    Tudo que aconteceu com esta pessoa, do mais recente para o mais antigo.

    Exige so "candidatos.ver": e informacao sobre o candidato, nao sobre o
    sistema. Quem pode abrir a ficha pode entender como ela chegou ali.
    """
    cand = db.get(models.Candidato, cand_id)
    if not cand:
        raise HTTPException(404, "Candidato não encontrado")
    return historico.montar(db, cand)


@router.get("/{cand_id}/pendencias", response_model=schemas.PendenciasResposta)
def pendencias(cand_id: int, aprovando: bool = False, db: Session = Depends(get_db),
               _: models.Usuario = Depends(require_perm("candidatos.ver"))):
    cand = db.get(models.Candidato, cand_id)
    if not cand:
        raise HTTPException(404, "Candidato não encontrado")
    lista = validacoes.pendencias_candidato(db, cand, aprovando=aprovando)
    return schemas.PendenciasResposta(
        pendencias=lista, bloqueia=bool(validacoes.importantes(lista)) and aprovando)
