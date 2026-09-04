"""Configuração de e-mail, modelos de mensagem e envio (e-mail / WhatsApp)."""
import re
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import require_perm, get_current_user
from ..audit import registrar
from .. import models, schemas, email_service as mail

router = APIRouter(tags=["Mensagens"])


@router.get("/email/config", response_model=schemas.ConfigEmailOut)
def ver_config(db: Session = Depends(get_db),
               _: models.Usuario = Depends(require_perm("email.configurar"))):
    cfg = mail.config(db)
    if not cfg:
        cfg = models.ConfigEmail()
        db.add(cfg); db.commit(); db.refresh(cfg)
    saida = schemas.ConfigEmailOut.model_validate(cfg)
    saida.tem_senha = bool(cfg.senha)
    return saida


@router.put("/email/config", response_model=schemas.ConfigEmailOut)
def salvar_config(dados: schemas.ConfigEmailIn, db: Session = Depends(get_db),
                  ator: models.Usuario = Depends(require_perm("email.configurar"))):
    cfg = mail.config(db) or models.ConfigEmail()
    campos = dados.model_dump()
    senha = campos.pop("senha", None)
    for k, v in campos.items():
        setattr(cfg, k, v)
    if senha:
        cfg.senha = senha
    if cfg.id is None:
        db.add(cfg)
    registrar(db, ator, "config_email", "email", None,
              {"servidor": cfg.servidor, "ativo": cfg.ativo})
    db.commit(); db.refresh(cfg)
    saida = schemas.ConfigEmailOut.model_validate(cfg)
    saida.tem_senha = bool(cfg.senha)
    return saida


@router.post("/email/testar")
def testar(db: Session = Depends(get_db),
           ator: models.Usuario = Depends(require_perm("email.configurar"))):
    """Manda um e-mail de teste para o próprio usuário."""
    ok, msg = mail.enviar(db, ator.email, "Teste de e-mail — ATS TLM",
                          "Se você recebeu esta mensagem, o envio está funcionando.",
                          tipo="teste")
    return {"sucesso": ok, "mensagem": msg}


@router.get("/modelos", response_model=list[schemas.ModeloOut])
def listar_modelos(canal: str | None = None, db: Session = Depends(get_db),
                   _: models.Usuario = Depends(get_current_user)):
    mail.semear_modelos(db)
    stmt = select(models.ModeloMensagem).order_by(models.ModeloMensagem.canal, models.ModeloMensagem.nome)
    if canal:
        stmt = stmt.where(models.ModeloMensagem.canal == canal)
    return db.scalars(stmt).all()


@router.post("/modelos", response_model=schemas.ModeloOut, status_code=201)
def criar_modelo(dados: schemas.ModeloIn, db: Session = Depends(get_db),
                 ator: models.Usuario = Depends(require_perm("listas.gerenciar"))):
    m = models.ModeloMensagem(**dados.model_dump())
    db.add(m); db.flush()
    registrar(db, ator, "criar_modelo", "modelo", m.id, {"nome": m.nome, "canal": m.canal})
    db.commit(); db.refresh(m)
    return m


@router.patch("/modelos/{mid}", response_model=schemas.ModeloOut)
def editar_modelo(mid: int, dados: schemas.ModeloUpdate, db: Session = Depends(get_db),
                  ator: models.Usuario = Depends(require_perm("listas.gerenciar"))):
    m = db.get(models.ModeloMensagem, mid)
    if not m:
        raise HTTPException(404, "Modelo não encontrado")
    for k, v in dados.model_dump(exclude_unset=True).items():
        setattr(m, k, v)
    registrar(db, ator, "editar_modelo", "modelo", m.id, {"nome": m.nome})
    db.commit(); db.refresh(m)
    return m


@router.delete("/modelos/{mid}", status_code=204)
def excluir_modelo(mid: int, db: Session = Depends(get_db),
                   _: models.Usuario = Depends(require_perm("listas.gerenciar"))):
    m = db.get(models.ModeloMensagem, mid)
    if not m:
        raise HTTPException(404, "Modelo não encontrado")
    db.delete(m); db.commit()


def normalizar_telefone(tel: str | None) -> str | None:
    """
    Deixa o telefone no formato do WhatsApp (55DDNNNNNNNNN).

    Trata os casos reais da planilha:
      "48 98851-0851"                 -> 5548988510851
      "48998118834.0" (Excel)         -> 5548998118834
      "(054) 9 9118 7080"             -> 5554991187080   (tira o zero do DDD)
      "81 98463-0580 | 48 98484-0137" -> usa o primeiro numero
      "5548988510851"                 -> mantem
    """
    if not tel:
        return None
    texto = str(tel).strip()
    texto = re.sub(r"\.0+$", "", texto)
    primeiro = re.split(r"[|;]| ou ", texto)[0]
    n = re.sub(r"\D", "", primeiro)
    if not n:
        return None
    if n.startswith("55") and len(n) in (12, 13):
        resto = n[2:]
    else:
        resto = n
    resto = resto.lstrip("0")
    if len(resto) not in (10, 11):
        return None
    return "55" + resto


def _link_whatsapp(tel: str | None, texto: str) -> str | None:
    n = normalizar_telefone(tel)
    return f"https://wa.me/{n}?text={quote(texto)}" if n else None


@router.post("/mensagens/previa", response_model=schemas.PreviaOut)
def previa(dados: schemas.EnviarIn, db: Session = Depends(get_db),
           ator: models.Usuario = Depends(require_perm("candidatos.ver"))):
    """Monta o texto com as variáveis preenchidas (sem enviar)."""
    cand = db.get(models.Candidato, dados.candidato_id)
    if not cand:
        raise HTTPException(404, "Candidato não encontrado")
    vaga = db.get(models.Vaga, cand.vaga_id) if cand.vaga_id else None
    v = mail.montar_variaveis(cand=cand, vaga=vaga, usuario=ator)
    assunto, corpo = dados.assunto, dados.corpo
    if dados.modelo_id:
        m = db.get(models.ModeloMensagem, dados.modelo_id)
        if not m:
            raise HTTPException(404, "Modelo não encontrado")
        assunto, corpo = m.assunto, m.corpo
    texto = mail.preencher(corpo or "", v)
    return schemas.PreviaOut(
        para=cand.email, assunto=mail.preencher(assunto or "", v), corpo=texto,
        telefone=cand.contato, link_whatsapp=_link_whatsapp(cand.contato, texto))


@router.post("/mensagens/enviar")
def enviar_email(dados: schemas.EnviarIn, db: Session = Depends(get_db),
                 ator: models.Usuario = Depends(require_perm("email.enviar"))):
    cand = db.get(models.Candidato, dados.candidato_id)
    if not cand:
        raise HTTPException(404, "Candidato não encontrado")
    if not cand.email:
        raise HTTPException(400, "Este candidato não tem e-mail cadastrado.")
    vaga = db.get(models.Vaga, cand.vaga_id) if cand.vaga_id else None
    v = mail.montar_variaveis(cand=cand, vaga=vaga, usuario=ator)
    assunto, corpo = dados.assunto, dados.corpo
    tipo = "manual"
    if dados.modelo_id:
        m = db.get(models.ModeloMensagem, dados.modelo_id)
        if not m:
            raise HTTPException(404, "Modelo não encontrado")
        assunto, corpo, tipo = m.assunto, m.corpo, (m.gatilho or "manual")
    ok, msg = mail.enviar(db, cand.email, mail.preencher(assunto or "", v),
                          mail.preencher(corpo or "", v), tipo=tipo, candidato_id=cand.id)
    if not ok:
        raise HTTPException(400, msg)
    registrar(db, ator, "enviar_email", "candidato", cand.id, {"tipo": tipo, "para": cand.email})
    db.commit()
    return {"sucesso": True, "mensagem": msg}


@router.get("/mensagens/enviados", response_model=list[schemas.EnvioOut])
def enviados(limite: int = 100, db: Session = Depends(get_db),
             _: models.Usuario = Depends(require_perm("email.enviar"))):
    return db.scalars(select(models.EnvioEmail)
                      .order_by(models.EnvioEmail.id.desc()).limit(limite)).all()


@router.post("/mensagens/rodar-automaticos")
def rodar_automaticos(db: Session = Depends(get_db),
                      ator: models.Usuario = Depends(require_perm("email.enviar"))):
    """
    Envia os avisos automáticos pendentes:
      - lembrete de entrevista para quem tem entrevista dentro das próximas N horas
      - aviso ao gestor sobre candidato parado esperando parecer
    Pode ser chamado manualmente pelo botão ou por uma tarefa agendada.
    """
    from datetime import datetime, timedelta
    cfg = mail.config(db)
    if not cfg or not cfg.ativo:
        raise HTTPException(400, "E-mail não está configurado ou está desativado.")
    mail.semear_modelos(db)
    agora = datetime.now()
    limite = agora + timedelta(hours=cfg.horas_antes or 24)
    resumo = {"lembretes": 0, "avisos_gestor": 0, "avisos_ti": 0, "falhas": 0}

    def modelo(gatilho, canal="email"):
        return db.scalar(select(models.ModeloMensagem).where(
            models.ModeloMensagem.gatilho == gatilho,
            models.ModeloMensagem.canal == canal,
            models.ModeloMensagem.ativo == True))

    FINAIS = {"APROVADO", "REPROVADO", "DECLINOU", "DESISTIU", "SEM RETORNO", "CANCELADO"}

    vagas_por_id = {v.id: v for v in db.scalars(select(models.Vaga)).all()}

    if cfg.lembrete_entrevista:
        m = modelo("lembrete")
        if m:
            for c in db.scalars(select(models.Candidato)).all():
                if (c.status or "").upper() in FINAIS or not c.email:
                    continue
                quando = c.data_2a_etapa or c.data_1a_etapa
                if not quando or not (agora <= quando <= limite):
                    continue
                if mail.ja_enviado(db, c.id, "lembrete"):
                    continue
                vaga = vagas_por_id.get(c.vaga_id) if c.vaga_id else None
                v = mail.montar_variaveis(cand=c, vaga=vaga, usuario=ator)
                ok, _ = mail.enviar(db, c.email, mail.preencher(m.assunto, v),
                                    mail.preencher(m.corpo, v), tipo="lembrete", candidato_id=c.id)
                resumo["lembretes" if ok else "falhas"] += 1

    if cfg.avisar_gestor:
        m = modelo("parecer")
        if m:
            emails_gestor = {g.nome: g.email for g in db.scalars(select(models.Gestor)).all() if g.email}
            for c in db.scalars(select(models.Candidato)).all():
                if (c.status or "").upper() in FINAIS:
                    continue
                aguarda = (c.status or "").upper().startswith("GEST") or \
                          "entrevista gest" in (c.etapa_atual or "").lower()
                if not aguarda:
                    continue
                destino = emails_gestor.get(c.gestor_nome)
                if not destino or mail.ja_enviado(db, c.id, "parecer"):
                    continue
                vaga = vagas_por_id.get(c.vaga_id) if c.vaga_id else None
                v = mail.montar_variaveis(cand=c, vaga=vaga, usuario=ator)
                ok, _ = mail.enviar(db, destino, mail.preencher(m.assunto, v),
                                    mail.preencher(m.corpo, v), tipo="parecer", candidato_id=c.id)
                resumo["avisos_gestor" if ok else "falhas"] += 1

    if getattr(cfg, "avisar_ti", False) and getattr(cfg, "email_ti", None):
        m = modelo("acessos")
        if m:
            pendentes = db.scalars(select(models.AcessoTI)
                                   .where(models.AcessoTI.status == "PENDENTE")).all()
            for a in pendentes:
                c = db.get(models.Candidato, a.candidato_id)
                if not c or mail.ja_enviado(db, c.id, "acessos"):
                    continue
                vaga = vagas_por_id.get(c.vaga_id) if c.vaga_id else None
                v = mail.montar_variaveis(cand=c, vaga=vaga, usuario=ator)
                ok, _ = mail.enviar(db, cfg.email_ti, mail.preencher(m.assunto, v),
                                    mail.preencher(m.corpo, v), tipo="acessos", candidato_id=c.id)
                resumo["avisos_ti" if ok else "falhas"] += 1

    registrar(db, ator, "disparo_automatico", "email", None, resumo)
    db.commit()
    return resumo
