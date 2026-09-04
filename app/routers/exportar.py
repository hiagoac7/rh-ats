"""
Exportação completa para Excel — garante que os dados nunca ficam presos no sistema.
Gera um .xlsx com uma aba por conjunto de dados, no mesmo espírito da planilha original.
"""
import io
from datetime import datetime, date
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from ..database import get_db
from ..deps import require_perm
from .. import models

router = APIRouter(tags=["Exportar"])

CAB_FILL = PatternFill("solid", fgColor="1C1917")
CAB_FONT = Font(color="FACC15", bold=True, size=10)


def _escreve(ws, cabecalhos, linhas):
    ws.append(cabecalhos)
    for c in range(1, len(cabecalhos) + 1):
        cel = ws.cell(row=1, column=c)
        cel.fill = CAB_FILL; cel.font = CAB_FONT
        cel.alignment = Alignment(horizontal="left", vertical="center")
    for l in linhas:
        ws.append(["" if v is None else v for v in l])
    for i, h in enumerate(cabecalhos, start=1):
        maior = len(str(h))
        for l in linhas:
            v = l[i - 1]
            if v is not None:
                maior = max(maior, min(len(str(v)), 45))
        ws.column_dimensions[get_column_letter(i)].width = min(maior + 2, 47)
    ws.freeze_panes = "A2"


def _d(v):
    """Datas viram date/datetime nativos do Excel; o resto vira texto."""
    if isinstance(v, (datetime, date)):
        return v
    return v


@router.get("/exportar/excel")
def exportar_excel(db: Session = Depends(get_db),
                   _: models.Usuario = Depends(require_perm("relatorios.exportar"))):
    wb = Workbook()
    vagas = db.scalars(select(models.Vaga)).all()
    cands = db.scalars(select(models.Candidato)).all()
    gestores = {g.id: g.nome for g in db.scalars(select(models.Gestor)).all()}
    vaga_cod = {v.id: (v.codigo or "") for v in vagas}

    ws = wb.active; ws.title = "CANDIDATOS"
    _escreve(ws,
        ["CANDIDATO", "VAGA", "Nº DE CONTATO", "CPF", "CONSULTA", "ORIGEM", "E-MAIL",
         "CONTATO INICIAL", "DATA 1ª ETAPA RH", "HORA 1ª ETAPA RH", "REAGENDADO?",
         "DATA/HORA REAGENDAMENTO", "PARECER", "DISC", "CHEK", "DATA 2ª ETAPA GESTÃO",
         "HORA 2ª ETAPA GESTÃO", "STATUS", "DEVOLUTIVA", "OBSERVAÇÕES", "ID VAGA",
         "ETAPA ATUAL", "GESTOR", "LINHA DO VENDEDOR", "DATA APROVAÇÃO", "BANCO DE TALENTOS"],
        [[c.nome, c.cargo, c.contato, c.cpf, c.consulta, c.origem, c.email,
          _d(c.contato_inicial), _d(c.data_1a_etapa), c.hora_1a_etapa, c.reagendado,
          c.reagendamento, c.parecer, c.disc, c.chek, _d(c.data_2a_etapa),
          c.hora_2a_etapa, c.status, c.devolutiva, c.observacoes, vaga_cod.get(c.vaga_id, ""),
          c.etapa_atual, c.gestor_nome, c.linha, _d(c.data_aprovacao),
          "sim" if c.banco_talentos else ""] for c in cands])

    ws = wb.create_sheet("VAGAS")
    def _cont(v, f):
        do = [c for c in cands if c.vaga_id == v.id]
        return f(do)
    _escreve(ws,
        ["ID DA VAGA", "ABERTURA", "PREVISÃO INÍCIO", "VAGA", "CARGO (padrão)", "NÍVEL", "QTDE",
         "TIPO", "MOTIVO", "SALÁRIO", "GESTOR", "ÁREA", "LINHA", "STATUS", "FECHAMENTO",
         "RANK", "RECEBIDOS", "ENTREV. RH", "ENTREV. GESTÃO", "APROVADOS", "OBSERVAÇÕES"],
        [[v.codigo, _d(v.data_abertura), _d(v.previsao_inicio), v.cargo, v.cargo_padrao, v.nivel,
          v.qtde, v.tipo, v.motivo, v.salario, gestores.get(v.gestor_id, ""), v.area, v.linha,
          v.status, _d(v.data_fechamento), v.rank,
          _cont(v, len),
          _cont(v, lambda d: sum(1 for c in d if c.data_1a_etapa)),
          _cont(v, lambda d: sum(1 for c in d if c.data_2a_etapa)),
          _cont(v, lambda d: sum(1 for c in d if (c.status or "").upper() == "APROVADO")),
          v.observacoes] for v in vagas])

    nomes = {c.id: c.nome for c in cands}
    anots = db.scalars(select(models.Anotacao).order_by(models.Anotacao.id)).all()
    ws = wb.create_sheet("ANOTAÇÕES")
    _escreve(ws, ["CANDIDATO", "AUTOR", "QUANDO", "ANOTAÇÃO"],
             [[nomes.get(a.candidato_id, ""), a.autor, _d(a.criado_em), a.texto] for a in anots])

    ws = wb.create_sheet("GESTORES")
    _escreve(ws, ["GESTOR", "E-MAIL"],
             [[g.nome, g.email] for g in db.scalars(select(models.Gestor).order_by(models.Gestor.nome)).all()])

    ws = wb.create_sheet("DIVULGAÇÃO")
    _escreve(ws, ["CANAL", "LINK", "USUÁRIO", "RESPONSÁVEL", "ATIVO", "OBSERVAÇÕES"],
             [[c.nome, c.link, c.login, c.responsavel, "sim" if c.ativo else "não", c.observacoes]
              for c in db.scalars(select(models.Canal).order_by(models.Canal.nome)).all()])

    canais = {c.id: c.nome for c in db.scalars(select(models.Canal)).all()}
    ws = wb.create_sheet("CANDIDATURAS")
    _escreve(ws, ["CANAL", "VAGA", "QUANTIDADE", "DATA", "OBSERVAÇÕES"],
             [[canais.get(r.canal_id, ""), vaga_cod.get(r.vaga_id, ""), r.quantidade, _d(r.data), r.observacoes]
              for r in db.scalars(select(models.Candidatura)).all()])

    ws = wb.create_sheet("LISTAS")
    _escreve(ws, ["TIPO", "VALOR", "ORDEM", "ATIVO"],
             [[l.tipo, l.valor, l.ordem, "sim" if l.ativo else "não"]
              for l in db.scalars(select(models.Lista).order_by(models.Lista.tipo, models.Lista.ordem)).all()])

    ws = wb.create_sheet("USUÁRIOS")
    _escreve(ws, ["NOME", "E-MAIL", "PERFIL", "ATIVO"],
             [[u.nome, u.email, u.perfil, "sim" if u.ativo else "não"]
              for u in db.scalars(select(models.Usuario).order_by(models.Usuario.nome)).all()])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    nome = f"ATS_TLM_{datetime.now():%Y-%m-%d_%H%M}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )
