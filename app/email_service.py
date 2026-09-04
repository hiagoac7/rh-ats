"""
Envio de e-mails do sistema.

Usa a biblioteca padrao do Python (smtplib) — nao precisa instalar nada.
A configuracao (servidor, usuario, senha de app) fica na tela Configuracoes.
Se o e-mail nao estiver configurado, o sistema segue funcionando normalmente:
apenas registra que nao foi possivel enviar.
"""
import re
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from sqlalchemy import select
from sqlalchemy.orm import Session
from . import models

MODELOS_PADRAO = [
    dict(nome="Convite para entrevista", canal="email", gatilho="convite",
         assunto="Entrevista para a vaga de {{vaga}} — {{empresa}}",
         corpo=("Olá, {{candidato}}!\n\n"
                "Tudo bem? Seguimos com seu processo para a vaga de {{vaga}}.\n"
                "Sua entrevista está marcada para {{data}} às {{hora}}.\n\n"
                "Por favor, confirme sua presença respondendo este e-mail.\n\n"
                "Até lá!\n{{remetente}}\n{{empresa}}")),
    dict(nome="Lembrete de entrevista", canal="email", gatilho="lembrete",
         assunto="Lembrete: sua entrevista é {{data}} às {{hora}}",
         corpo=("Olá, {{candidato}}!\n\n"
                "Passando para lembrar da sua entrevista para a vaga de {{vaga}},\n"
                "marcada para {{data}} às {{hora}}.\n\n"
                "Se precisar remarcar, é só responder este e-mail.\n\n"
                "Até breve!\n{{remetente}}\n{{empresa}}")),
    dict(nome="Devolutiva — não seguimos", canal="email", gatilho="devolutiva",
         assunto="Retorno sobre o processo seletivo — {{vaga}}",
         corpo=("Olá, {{candidato}}!\n\n"
                "Agradecemos muito seu interesse na vaga de {{vaga}} e o tempo que dedicou "
                "ao nosso processo.\n\n"
                "Neste momento seguiremos com outro perfil, mas seu currículo fica guardado "
                "em nosso banco de talentos para futuras oportunidades.\n\n"
                "Desejamos sucesso na sua trajetória!\n\n"
                "Atenciosamente,\n{{remetente}}\n{{empresa}}")),
    dict(nome="Aviso ao gestor — parecer pendente", canal="email", gatilho="parecer",
         assunto="Parecer pendente: {{candidato}} — {{vaga}}",
         corpo=("Olá, {{gestor}}!\n\n"
                "O candidato {{candidato}}, da vaga de {{vaga}}, está aguardando seu parecer "
                "desde {{data}} ({{dias}} dia(s)).\n\n"
                "Contato do candidato: {{contato}}\n\n"
                "Assim que possível, registre o retorno para darmos sequência.\n\n"
                "Obrigado!\n{{remetente}}")),
    dict(nome="Aviso ao TI — novo contratado", canal="email", gatilho="acessos",
         assunto="Novo contratado: {{candidato}} — liberar acessos",
         corpo=("Olá, time de TI!\n\n"
                "O candidato abaixo foi aprovado e precisa dos acessos liberados:\n\n"
                "  Nome ........: {{candidato}}\n"
                "  Cargo .......: {{vaga}}\n"
                "  Área ........: {{area}}\n"
                "  Gestor ......: {{gestor}}\n"
                "  Início ......: {{inicio}}\n"
                "  E-mail ......: {{email}}\n"
                "  Telefone ....: {{contato}}\n\n"
                "Abra o sistema em Acessos para ver a lista do que precisa ser criado.\n\n"
                "{{remetente}}\n{{empresa}}")),
    dict(nome="Convite (WhatsApp)", canal="whatsapp", gatilho="convite",
         assunto=None,
         corpo=("Olá, {{candidato}}! Aqui é {{remetente}}, da {{empresa}}. "
                "Sua entrevista para a vaga de {{vaga}} está marcada para {{data}} às {{hora}}. "
                "Consegue confirmar, por favor?")),
    dict(nome="Lembrete (WhatsApp)", canal="whatsapp", gatilho="lembrete",
         assunto=None,
         corpo=("Oi, {{candidato}}! Passando para lembrar da sua entrevista de {{vaga}} "
                "amanhã, {{data}}, às {{hora}}. Até lá!")),
]


def semear_modelos(db: Session):
    if db.query(models.ModeloMensagem).count() == 0:
        for m in MODELOS_PADRAO:
            db.add(models.ModeloMensagem(**m))
        db.commit()


def montar_variaveis(cand=None, vaga=None, usuario=None, empresa="TLM Equipamentos", extra=None):
    def data_br(d):
        if not d:
            return ""
        return d.strftime("%d/%m/%Y")
    v = {
        "empresa": empresa,
        "remetente": getattr(usuario, "nome", "") or "Equipe de RH",
        "candidato": getattr(cand, "nome", "") or "",
        "contato": getattr(cand, "contato", "") or "",
        "email": getattr(cand, "email", "") or "",
        "vaga": (getattr(vaga, "cargo_padrao", None) or getattr(vaga, "cargo", None)
                 or getattr(cand, "cargo", "") or ""),
        "gestor": getattr(cand, "gestor_nome", "") or "",
        "data": "",
        "hora": "",
        "dias": str(getattr(cand, "dias_parado", "") or ""),
        "area": getattr(vaga, "area", "") or "",
        "inicio": data_br(getattr(vaga, "previsao_inicio", None)) or "a definir",
    }
    if cand is not None:
        d2, d1 = getattr(cand, "data_2a_etapa", None), getattr(cand, "data_1a_etapa", None)
        if d2:
            v["data"], v["hora"] = data_br(d2), (cand.hora_2a_etapa or "")
        elif d1:
            v["data"], v["hora"] = data_br(d1), (cand.hora_1a_etapa or "")
    if extra:
        v.update({k: str(x) for k, x in extra.items()})
    return v


def preencher(texto: str, variaveis: dict) -> str:
    """Troca {{campo}} pelos valores. Campo desconhecido vira vazio."""
    if not texto:
        return ""
    return re.sub(r"\{\{\s*(\w+)\s*\}\}", lambda m: str(variaveis.get(m.group(1), "")), texto)


def config(db: Session) -> models.ConfigEmail | None:
    return db.scalar(select(models.ConfigEmail).limit(1))


def enviar(db: Session, para: str, assunto: str, corpo: str,
           tipo: str = "manual", candidato_id: int | None = None) -> tuple[bool, str]:
    """Envia um e-mail. Devolve (sucesso, mensagem). Nunca levanta excecao."""
    cfg = config(db)
    if not cfg or not cfg.ativo or not cfg.servidor or not cfg.usuario:
        return False, "E-mail não configurado. Configure em Configurações → E-mail."
    if not para:
        return False, "Destinatário sem e-mail cadastrado."

    msg = EmailMessage()
    msg["From"] = f'{cfg.nome_remetente or "RH"} <{cfg.remetente or cfg.usuario}>'
    msg["To"] = para
    msg["Subject"] = assunto or "(sem assunto)"
    msg.set_content(corpo or "")

    sucesso, erro = True, None
    try:
        contexto = ssl.create_default_context()
        if int(cfg.porta) == 465:
            with smtplib.SMTP_SSL(cfg.servidor, int(cfg.porta), context=contexto, timeout=20) as s:
                s.login(cfg.usuario, cfg.senha or "")
                s.send_message(msg)
        else:
            with smtplib.SMTP(cfg.servidor, int(cfg.porta), timeout=20) as s:
                s.starttls(context=contexto)
                s.login(cfg.usuario, cfg.senha or "")
                s.send_message(msg)
    except Exception as e:
        sucesso, erro = False, f"{type(e).__name__}: {e}"

    db.add(models.EnvioEmail(para=para, assunto=assunto, tipo=tipo,
                             candidato_id=candidato_id, sucesso=sucesso, erro=erro))
    db.commit()
    return sucesso, ("Enviado." if sucesso else f"Falha ao enviar — {erro}")


def ja_enviado(db: Session, candidato_id: int, tipo: str) -> bool:
    """Evita mandar o mesmo aviso duas vezes para a mesma pessoa."""
    return db.scalar(
        select(models.EnvioEmail).where(models.EnvioEmail.candidato_id == candidato_id,
                                        models.EnvioEmail.tipo == tipo,
                                        models.EnvioEmail.sucesso == True)
    ) is not None
