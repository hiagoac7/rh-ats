"""
Linha do tempo de um candidato.

Junta em ordem cronológica tudo que se sabe sobre uma pessoa:

  * marcos do próprio cadastro  — contato inicial, entrevistas, aprovação
  * o que a auditoria registrou — quem mudou o quê e quando
  * as anotações do recrutador

Nada disso é campo novo: é leitura do que o sistema já grava. A ideia veio de
uma pergunta simples que a tela não respondia — "o que já aconteceu com esta
pessoa?" — e que hoje obriga o RH a cruzar três lugares diferentes.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models

ROTULOS = {
    "status": "Status",
    "etapa_atual": "Etapa",
    "parecer": "Parecer",
    "devolutiva": "Devolutiva",
    "disc": "DISC",
    "consulta": "Consulta",
    "chek": "Check",
    "gestor_nome": "Gestor",
    "vaga_id": "Vaga",
    "data_1a_etapa": "Data da 1ª etapa",
    "hora_1a_etapa": "Hora da 1ª etapa",
    "data_2a_etapa": "Data da 2ª etapa",
    "hora_2a_etapa": "Hora da 2ª etapa",
    "data_aprovacao": "Data de aprovação",
    "contato_inicial": "Contato inicial",
    "banco_talentos": "Banco de talentos",
    "observacoes": "Observações",
    "linha": "Linha",
    "reagendado": "Reagendado",
    "nome": "Nome",
    "email": "E-mail",
    "contato": "Telefone",
    "cpf": "CPF",
    "origem": "Origem",
    "cargo": "Cargo",
}

IGNORAR = {"versao", "confirmar_pendencias", "confirmar_duplicado", "extras"}


def _quando(v) -> datetime | None:
    if isinstance(v, datetime):
        return v
    if isinstance(v, date):
        return datetime(v.year, v.month, v.day)
    return None


def _valor_legivel(campo: str, valor) -> str:
    if valor is None or valor == "":
        return "(vazio)"
    if isinstance(valor, bool):
        return "sim" if valor else "não"
    if campo.startswith("data_") or campo == "contato_inicial":
        texto = str(valor)[:10]
        partes = texto.split("-")
        return f"{partes[2]}/{partes[1]}/{partes[0]}" if len(partes) == 3 else texto
    return str(valor)


def montar(db: Session, cand: models.Candidato) -> list[dict]:
    """
    Devolve os acontecimentos do mais recente para o mais antigo.

    Cada item: {quando, tipo, titulo, detalhe, quem}
    """
    itens: list[dict] = []

    marcos = [
        (cand.contato_inicial, "contato", "Primeiro contato", None),
        (cand.data_1a_etapa, "entrevista", "Entrevista com o RH",
         cand.hora_1a_etapa and f"às {cand.hora_1a_etapa}"),
        (cand.data_2a_etapa, "entrevista", "Entrevista com a gestão",
         " · ".join(x for x in [cand.hora_2a_etapa and f"às {cand.hora_2a_etapa}",
                                cand.gestor_nome] if x) or None),
        (cand.data_aprovacao, "aprovacao", "Aprovado", None),
    ]
    for quando, tipo, titulo, detalhe in marcos:
        dt = _quando(quando)
        if dt:
            itens.append({"quando": dt, "tipo": tipo, "titulo": titulo,
                          "detalhe": detalhe, "quem": None})

    registros = db.scalars(
        select(models.Auditoria).where(
            models.Auditoria.entidade == "candidato",
            models.Auditoria.entidade_id == str(cand.id),
        ).order_by(models.Auditoria.id)
    ).all()
    for r in registros:
        det = r.detalhes or {}
        campos = {k: v for k, v in det.items() if k not in IGNORAR} if isinstance(det, dict) else {}
        if r.acao == "criar_candidato":
            itens.append({"quando": r.criado_em, "tipo": "criado",
                          "titulo": "Cadastrado no sistema", "detalhe": None,
                          "quem": r.ator_nome})
            continue
        if r.acao == "excluir_candidato":
            continue
        if not campos:
            continue
        for campo, valor in campos.items():
            itens.append({
                "quando": r.criado_em,
                "tipo": "alteracao",
                "titulo": f"{ROTULOS.get(campo, campo)} → {_valor_legivel(campo, valor)}",
                "detalhe": None,
                "quem": r.ator_nome,
            })

    for a in db.scalars(
        select(models.Anotacao).where(models.Anotacao.candidato_id == cand.id)
    ).all():
        itens.append({"quando": a.criado_em, "tipo": "anotacao",
                      "titulo": "Anotação", "detalhe": a.texto, "quem": a.autor})

    itens.sort(key=lambda x: x["quando"] or datetime.min, reverse=True)
    return itens
