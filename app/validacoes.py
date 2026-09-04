"""
Avisos de informação faltando.

O sistema nao impede o RH de trabalhar, mas em dois momentos importantes
— fechar uma vaga e aprovar um candidato — ele confere o que ficou em branco
e pede uma confirmacao consciente antes de seguir.

Cada pendencia tem:
  campo   : nome tecnico (para o front focar no campo certo)
  rotulo  : texto que o usuario le
  porque  : explica o impacto de deixar em branco
  nivel   : "importante" (pede confirmacao) ou "aviso" (so informa)
"""
from sqlalchemy.orm import Session
from . import models


def _vazio(v) -> bool:
    return v is None or (isinstance(v, str) and not v.strip())


def pendencias_vaga(db: Session, vaga: models.Vaga, fechando: bool = False) -> list[dict]:
    """O que falta preencher numa vaga (mais rigoroso quando esta fechando)."""
    p: list[dict] = []

    if _vazio(vaga.previsao_inicio):
        p.append(dict(campo="previsao_inicio", rotulo="Previsão de início",
                      porque="O TI usa esta data para preparar os acessos do novo contratado a tempo.",
                      nivel="importante"))
    if _vazio(vaga.gestor_id):
        p.append(dict(campo="gestor_id", rotulo="Gestor responsável",
                      porque="Sem gestor, ninguém recebe o aviso de parecer pendente.",
                      nivel="importante"))
    if _vazio(vaga.data_abertura):
        p.append(dict(campo="data_abertura", rotulo="Data de abertura",
                      porque="Sem ela não dá para calcular há quantos dias a vaga está aberta nem o SLA.",
                      nivel="importante"))
    if _vazio(vaga.salario):
        p.append(dict(campo="salario", rotulo="Salário",
                      porque="Usado nos relatórios de custo e na comparação entre vagas.",
                      nivel="aviso"))
    if _vazio(vaga.area):
        p.append(dict(campo="area", rotulo="Área",
                      porque="Os relatórios por área ficam incompletos.", nivel="aviso"))
    if _vazio(vaga.motivo):
        p.append(dict(campo="motivo", rotulo="Motivo da vaga",
                      porque="É o que mostra se a empresa está crescendo ou repondo saídas.",
                      nivel="aviso"))
    if _vazio(vaga.cargo_padrao):
        p.append(dict(campo="cargo_padrao", rotulo="Cargo padrão",
                      porque="Sem ele a vaga não agrupa com as outras aberturas do mesmo cargo.",
                      nivel="aviso"))

    if fechando:
        if _vazio(vaga.data_fechamento):
            p.append(dict(campo="data_fechamento", rotulo="Data de fechamento",
                          porque="Necessária para calcular quanto tempo a vaga levou para ser preenchida.",
                          nivel="importante"))
        aprovados = db.query(models.Candidato).filter(
            models.Candidato.vaga_id == vaga.id,
            models.Candidato.status.ilike("APROVADO")).count()
        if aprovados == 0:
            p.append(dict(campo="", rotulo="Nenhum candidato aprovado nesta vaga",
                          porque="Se a vaga foi preenchida, marque o candidato como aprovado antes de fechar.",
                          nivel="importante"))
        elif aprovados < (vaga.qtde or 1):
            p.append(dict(campo="qtde", rotulo=f"Só {aprovados} de {vaga.qtde or 1} posições preenchidas",
                          porque="Confirme se a quantidade da vaga está certa ou se faltou aprovar alguém.",
                          nivel="aviso"))
    return p


def pendencias_candidato(db: Session, cand: models.Candidato, aprovando: bool = False) -> list[dict]:
    """O que falta num candidato (mais rigoroso quando esta sendo aprovado)."""
    p: list[dict] = []

    if _vazio(cand.contato) and _vazio(cand.email):
        p.append(dict(campo="contato", rotulo="Telefone ou e-mail",
                      porque="Sem contato não é possível avisar o candidato nem enviar a devolutiva.",
                      nivel="importante"))
    if _vazio(cand.origem):
        p.append(dict(campo="origem", rotulo="Origem",
                      porque="É o que mostra qual canal de divulgação traz bons candidatos.",
                      nivel="aviso"))

    if aprovando:
        if _vazio(cand.vaga_id):
            p.append(dict(campo="vaga_id", rotulo="Vaga vinculada",
                          porque="Sem vaga, a contratação não entra nos indicadores nem gera o pedido de acesso completo.",
                          nivel="importante"))
        if _vazio(cand.data_aprovacao) and _vazio(cand.data_2a_etapa):
            p.append(dict(campo="data_aprovacao", rotulo="Data de aprovação",
                          porque="Necessária para calcular o tempo de contratação.",
                          nivel="importante"))
        if _vazio(cand.email):
            p.append(dict(campo="email", rotulo="E-mail do candidato",
                          porque="O TI costuma precisar dele para criar o acesso corporativo.",
                          nivel="aviso"))
        if _vazio(cand.cpf):
            p.append(dict(campo="cpf", rotulo="CPF",
                          porque="Necessário para a admissão.", nivel="aviso"))
        vaga = db.get(models.Vaga, cand.vaga_id) if cand.vaga_id else None
        if vaga and _vazio(vaga.previsao_inicio):
            p.append(dict(campo="previsao_inicio_vaga", rotulo="Previsão de início (na vaga)",
                          porque="Sem esta data o TI não sabe para quando preparar os acessos.",
                          nivel="importante"))
    return p


def importantes(pendencias: list[dict]) -> list[dict]:
    return [x for x in pendencias if x.get("nivel") == "importante"]
