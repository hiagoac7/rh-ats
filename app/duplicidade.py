"""
Evita cadastrar duas vezes a mesma pessoa ou a mesma vaga.

Nao bloqueia de forma cega: mostra o que ja existe e deixa o RH decidir,
porque as vezes duas pessoas tem mesmo o mesmo nome.
"""
import re
import unicodedata
from sqlalchemy import select
from sqlalchemy.orm import Session
from . import models


def _normalizar(texto: str | None) -> str:
    """Tira acento, pontuacao e espacos extras para comparar nomes de verdade."""
    if not texto:
        return ""
    t = unicodedata.normalize("NFKD", str(texto))
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-zA-Z0-9 ]", " ", t)
    return " ".join(t.lower().split())


def _so_digitos(v: str | None) -> str:
    return re.sub(r"\D", "", v or "")


def candidatos_parecidos(db: Session, nome: str, cpf: str | None = None,
                         email: str | None = None, contato: str | None = None,
                         ignorar_id: int | None = None) -> list[dict]:
    """
    Procura candidatos que provavelmente sao a mesma pessoa.

    Confere, nesta ordem de confianca: CPF, e-mail, telefone e nome.
    """
    achados: dict[int, dict] = {}
    todos = db.scalars(select(models.Candidato)).all()

    alvo_nome = _normalizar(nome)
    alvo_cpf = _so_digitos(cpf)
    alvo_mail = (email or "").strip().lower()
    alvo_tel = _so_digitos(contato)[-8:]

    for c in todos:
        if ignorar_id and c.id == ignorar_id:
            continue
        motivo = None
        if alvo_cpf and len(alvo_cpf) >= 11 and _so_digitos(c.cpf) == alvo_cpf:
            motivo = "mesmo CPF"
        elif alvo_mail and (c.email or "").strip().lower() == alvo_mail:
            motivo = "mesmo e-mail"
        elif alvo_tel and len(alvo_tel) >= 8 and _so_digitos(c.contato)[-8:] == alvo_tel:
            motivo = "mesmo telefone"
        elif alvo_nome and _normalizar(c.nome) == alvo_nome:
            motivo = "mesmo nome"
        if motivo:
            achados[c.id] = {
                "id": c.id, "nome": c.nome, "motivo": motivo,
                "cargo": c.cargo, "status": c.status, "etapa_atual": c.etapa_atual,
                "contato": c.contato, "email": c.email,
            }
    return list(achados.values())


def vagas_parecidas(db: Session, codigo: str | None, cargo: str | None,
                    cargo_padrao: str | None = None) -> list[dict]:
    """Procura vagas com o mesmo codigo (sempre erro) ou aberta ha pouco para o mesmo cargo."""
    achados = []
    if codigo:
        igual = db.scalar(select(models.Vaga).where(models.Vaga.codigo == codigo))
        if igual:
            achados.append({"id": igual.id, "codigo": igual.codigo, "cargo": igual.cargo,
                            "status": igual.status, "motivo": "já existe uma vaga com este código"})
    alvo = _normalizar(cargo_padrao or cargo)
    if alvo:
        for v in db.scalars(select(models.Vaga)).all():
            if (v.status or "").upper() == "FECHADA":
                continue
            if _normalizar(v.cargo_padrao or v.cargo) == alvo and not any(a["id"] == v.id for a in achados):
                achados.append({"id": v.id, "codigo": v.codigo, "cargo": v.cargo,
                                "status": v.status, "motivo": "já existe uma vaga aberta para este cargo"})
    return achados
