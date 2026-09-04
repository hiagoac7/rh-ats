"""
Importa os dados da planilha Automacao_RH_v17.xlsx para o banco.

Uso:
    python -m scripts.importar_planilha caminho/para/Automacao_RH_v17.xlsx

Le as abas VAGAS, CANDIDATOS, CICLOS VENDEDOR/SDR e LISTAS e popula as tabelas.
Idempotente por chave natural (codigo da vaga / nome+cargo do candidato).
"""
import os
import sys
from datetime import datetime, date
import openpyxl

sys.path.insert(0, ".")
from app.database import SessionLocal
from app.esquema import preparar
from app import models


def as_date(v):
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    return None

def as_datetime(v):
    if isinstance(v, datetime):
        return v
    if isinstance(v, date):
        return datetime(v.year, v.month, v.day)
    return None

def _chave(nome):
    """Normaliza o nome para comparar (ignora caixa e espacos extras)."""
    return " ".join(str(nome or "").split()).lower()


def _chave_pessoa(nome, email=None):
    """
    Identidade estavel de um candidato para a memoria da importacao.

    NAO usa a vaga de proposito: o RH move gente de uma vaga para outra dentro
    do sistema, e se a chave dependesse disso a pessoa pareceria novidade no
    import seguinte — voltando duplicada. Nome + e-mail e o que nao muda.
    """
    e = str(email or "").strip().lower()
    return f"{_chave(nome)}|{e}"


class Memoria:
    """
    Lembra o que a planilha ja trouxe alguma vez.

    O problema que isto resolve: a planilha continua com linhas que o RH ja
    limpou no sistema (aberturas antigas de VENDEDOR, candidatos duplicados,
    vagas de teste). Sem memoria, todo import ressuscitava tudo e desorganizava
    o site de novo.

    Regra:
      chave nunca vista            -> e novidade, importa
      chave vista e ainda no banco -> atualiza normalmente
      chave vista e sumida         -> foi removida de proposito, IGNORA
    """

    def __init__(self, db, refazer=False):
        self.db = db
        self.refazer = refazer
        self.vistas = {}
        for r in db.query(models.JaImportado).all():
            self.vistas.setdefault(r.tipo, set()).add(r.chave)
        self.ignorados = {"vaga": [], "candidato": []}
        self.primeira_vez = not self.vistas
        if self.primeira_vez:
            self._semear()

    def _semear(self):
        """
        Primeira execucao: registra o que JA existe no sistema.

        Sem isto, a memoria comecaria vazia e a importacao seguinte trataria
        os 300+ registros existentes como novidade. Note que so da para semear
        o que esta no banco AGORA — o que foi apagado antes desta funcao existir
        vai voltar uma ultima vez. Depois de apagar de novo, nao volta mais.
        """
        n = 0
        for v in self.db.query(models.Vaga).all():
            chave = v.codigo or v.cargo
            if chave:
                self.db.add(models.JaImportado(tipo="vaga", chave=chave))
                self.vistas.setdefault("vaga", set()).add(chave)
                n += 1
        for c in self.db.query(models.Candidato).all():
            chave = _chave_pessoa(c.nome, c.email)
            self.db.add(models.JaImportado(tipo="candidato", chave=chave))
            self.vistas.setdefault("candidato", set()).add(chave)
            n += 1
        self.db.commit()
        print(f"Primeira importacao com memoria: registrei {n} itens que ja estavam no sistema.")
        print("  A partir de agora, o que voce apagar aqui nao volta mais da planilha.")

    def conhecida(self, tipo, chave):
        return chave in self.vistas.get(tipo, set())

    def deve_criar(self, tipo, chave, rotulo=None):
        """False quando a chave ja veio antes e nao esta mais no sistema."""
        if self.refazer:
            return True
        if self.conhecida(tipo, chave):
            self.ignorados[tipo].append(rotulo or chave)
            return False
        return True

    def anotar(self, tipo, chave):
        if not chave or self.conhecida(tipo, chave):
            return
        self.db.add(models.JaImportado(tipo=tipo, chave=chave))
        self.vistas.setdefault(tipo, set()).add(chave)


def as_hora(v):
    """Normaliza hora: time(16,15) -> '16:15' | '16h30' -> '16:30' | '-' -> None."""
    from datetime import time as _t, datetime as _dt
    if v is None:
        return None
    if isinstance(v, _dt):
        return v.strftime("%H:%M") if (v.hour or v.minute) else None
    if isinstance(v, _t):
        return v.strftime("%H:%M") if (v.hour or v.minute) else None
    s = str(v).strip().lower().replace("h", ":").replace(".", ":")
    s = s.rstrip(":")
    if not s or s == "-":
        return None
    partes = s.split(":")
    try:
        h = int(partes[0]); m = int(partes[1]) if len(partes) > 1 and partes[1] else 0
        if 0 <= h <= 23 and 0 <= m <= 59:
            return f"{h:02d}:{m:02d}"
    except ValueError:
        pass
    return None


def clean(v):
    if v is None:
        return None
    s = str(v).strip()
    return None if s in {"", "-"} else s

def as_int(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None

def as_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def importar(caminho: str, refazer: bool = False):
    import datetime as _dt
    if not os.path.exists(caminho):
        print(f"ERRO: arquivo nao encontrado: {caminho}")
        sys.exit(1)

    quando = _dt.datetime.fromtimestamp(os.path.getmtime(caminho))
    print(f"Arquivo : {os.path.abspath(caminho)}")
    print(f"Alterado: {quando:%d/%m/%Y %H:%M}")
    preparar()
    wb = openpyxl.load_workbook(caminho, data_only=True)
    db = SessionLocal()
    memoria = Memoria(db, refazer=refazer)
    if refazer:
        print("MODO REFAZER: tudo da planilha sera recriado, inclusive o que")
        print("              voce tinha removido no sistema.")

    gestores: dict[str, models.Gestor] = {}

    def get_gestor(nome, email=None):
        nome = clean(nome)
        if not nome:
            return None
        if nome not in gestores:
            g = db.query(models.Gestor).filter_by(nome=nome).first()
            if not g:
                g = models.Gestor(nome=nome, email=clean(email))
                db.add(g)
                db.flush()
            gestores[nome] = g
        return gestores[nome]

    if "LISTAS" in wb.sheetnames:
        ws = wb["LISTAS"]
        for row in ws.iter_rows(min_row=2, values_only=True):
            gestor_nome = row[9] if len(row) > 9 else None
            gestor_email = row[10] if len(row) > 10 else None
            if clean(gestor_nome):
                get_gestor(gestor_nome, gestor_email)

    vagas_por_codigo: dict[str, models.Vaga] = {}
    if "VAGAS" in wb.sheetnames:
        ws = wb["VAGAS"]
        for row in ws.iter_rows(min_row=4, values_only=True):
            cargo = clean(row[2])
            codigo = clean(row[20])
            if not cargo and not codigo:
                continue
            vaga = None
            if codigo:
                vaga = vagas_por_codigo.get(codigo) or db.query(models.Vaga).filter_by(codigo=codigo).first()
            if not vaga:
                if not memoria.deve_criar("vaga", codigo or cargo, f"{codigo or ''} {cargo or ''}".strip()):
                    continue
                vaga = models.Vaga(codigo=codigo, cargo=cargo or codigo)
                db.add(vaga)
            memoria.anotar("vaga", codigo or cargo)
            vaga.cargo = cargo or vaga.cargo
            vaga.cargo_padrao = clean(row[21]) if len(row) > 21 else None
            vaga.nivel = clean(row[3])
            vaga.qtde = as_int(row[4]) or 1
            vaga.tipo = clean(row[5])
            vaga.motivo = clean(row[6])
            vaga.salario = as_float(row[7])
            vaga.area = clean(row[9])
            vaga.status = clean(row[10])
            vaga.data_abertura = as_date(row[0])
            vaga.previsao_inicio = as_date(row[1])
            vaga.data_fechamento = as_date(row[11])
            vaga.observacoes = clean(row[19])
            vaga.linha = clean(row[24]) if len(row) > 24 else None
            vaga.rank = as_int(row[23]) if len(row) > 23 else None
            g = get_gestor(row[8])
            vaga.gestor = g
            db.flush()
            if codigo:
                vagas_por_codigo[codigo] = vaga

    novos = atualizados = 0
    if "CANDIDATOS" in wb.sheetnames:
        ws = wb["CANDIDATOS"]
        existentes = {}
        for c in db.query(models.Candidato).all():
            existentes.setdefault((_chave(c.nome), c.vaga_id), c)
        for row in ws.iter_rows(min_row=2, values_only=True):
            nome = clean(row[0])
            if not nome:
                continue
            id_vaga = clean(row[21]) if len(row) > 21 else None
            vaga = vagas_por_codigo.get(id_vaga) if id_vaga else None
            campos = dict(
                nome=nome,
                cargo=clean(row[1]),
                contato=clean(row[2]),
                cpf=clean(row[3]),
                origem=clean(row[5]),
                email=clean(row[6]),
                contato_inicial=as_date(row[7]),
                data_1a_etapa=as_datetime(row[8]),
                hora_1a_etapa=as_hora(row[9]) or as_hora(row[8]),
                data_2a_etapa=as_datetime(row[15]),
                hora_2a_etapa=as_hora(row[16]),
                parecer=clean(row[12]),
                disc=clean(row[13]),
                consulta=clean(row[4]),
                chek=clean(row[14]),
                reagendado=clean(row[10]),
                reagendamento=clean(row[11]),
                status=clean(row[17]),
                devolutiva=clean(row[18]),
                observacoes=clean(row[19]),
                etapa_atual=clean(row[22]) if len(row) > 22 else None,
                gestor_nome=clean(row[24]) if len(row) > 24 else None,
                data_aprovacao=as_date(row[29]) if len(row) > 29 else None,
                linha=clean(row[27]) if len(row) > 27 else None,
            )
            chave = (_chave(nome), vaga.id if vaga else None)
            chave_mem = _chave_pessoa(nome, campos.get("email"))
            cand = existentes.get(chave)
            if cand:
                for k, v in campos.items():
                    setattr(cand, k, v)
                cand.vaga = vaga
                atualizados += 1
            else:
                if not memoria.deve_criar("candidato", chave_mem, nome):
                    continue
                cand = models.Candidato(**campos, vaga=vaga)
                db.add(cand)
                db.flush()
                existentes[chave] = cand
                novos += 1
            memoria.anotar("candidato", chave_mem)

    def importar_ciclos(aba, codigo_vaga):
        if aba not in wb.sheetnames:
            return
        vaga = vagas_por_codigo.get(codigo_vaga)
        if not vaga:
            vaga = db.query(models.Vaga).filter_by(codigo=codigo_vaga).first()
        if not vaga:
            return
        vagas_por_codigo[codigo_vaga] = vaga
        ws = wb[aba]
        for row in ws.iter_rows(min_row=5, values_only=True):
            abertura = as_date(row[2])
            if abertura is None:
                continue
            db.add(models.CicloVaga(
                vaga=vaga,
                linha=clean(row[1]),
                data_abertura=abertura,
                data_fechamento=as_date(row[3]),
                candidatos=as_int(row[4]),
                aprovados=as_int(row[5]),
                status=clean(row[8]),
                observacoes=clean(row[9]),
            ))

    db.query(models.CicloVaga).delete()
    if "LISTAS" in wb.sheetnames:
        wsl = wb["LISTAS"]
        for row in wsl.iter_rows(min_row=2, values_only=True):
            cargo = clean(row[8]) if len(row) > 8 else None
            gestor = clean(row[9]) if len(row) > 9 else None
            if not cargo or not gestor:
                continue
            m = db.query(models.MapaCargoGestor).filter_by(cargo=cargo).first()
            if m:
                m.gestor = gestor
            else:
                db.add(models.MapaCargoGestor(cargo=cargo, gestor=gestor))

    if "DIVULGAÇÃO" in wb.sheetnames:
        wsd = wb["DIVULGAÇÃO"]
        for row in wsd.iter_rows(min_row=6, max_row=16, values_only=True):
            nome = clean(row[0]) if row else None
            if not nome or nome.lower().startswith("cvs recebidos"):
                continue
            existe = db.query(models.Canal).filter_by(nome=nome).first()
            if existe:
                continue
            info = clean(row[1]) if len(row) > 1 else None
            link = info if (info or "").startswith("http") else None
            login = None if link else info
            db.add(models.Canal(nome=nome, link=link, login=login, ativo=True))

    importar_ciclos("CICLOS VENDEDOR", "V030")
    importar_ciclos("CICLOS SDR", "SDR")

    removidas = 0
    for v in db.query(models.Vaga).all():
        codigo_ok = bool(v.codigo) and v.codigo[0].upper() == "V" and v.codigo[1:].isdigit()
        tem_dados = v.data_abertura or v.salario or v.gestor_id
        tem_cands = db.query(models.Candidato).filter_by(vaga_id=v.id).count() > 0
        if not codigo_ok and not tem_dados and not tem_cands:
            db.query(models.CicloVaga).filter_by(vaga_id=v.id).delete()
            db.delete(v)
            removidas += 1

    db.commit()

    print("Importacao concluida:")
    if removidas:
        print(f"  vagas fantasma removidas: {removidas}")
    print(f"  candidatos novos: {novos} | atualizados: {atualizados}")

    ig_v = memoria.ignorados["vaga"]
    ig_c = memoria.ignorados["candidato"]
    if ig_v or ig_c:
        print()
        print("  NAO recriados (voce removeu no sistema, a planilha ainda tem):")
        if ig_v:
            print(f"    vagas ......: {len(ig_v)}")
            for x in ig_v[:6]:
                print(f"       - {x}")
            if len(ig_v) > 6:
                print(f"       ... e mais {len(ig_v)-6}")
        if ig_c:
            print(f"    candidatos .: {len(ig_c)}")
            for x in ig_c[:6]:
                print(f"       - {x}")
            if len(ig_c) > 6:
                print(f"       ... e mais {len(ig_c)-6}")
        print()
        print("    Isso e proposital: o sistema manda mais que a planilha.")
        print("    Para trazer tudo de volta assim mesmo, rode com  --refazer")
    if novos == 0 and atualizados > 0:
        print()
        print("  AVISO: nenhum candidato NOVO foi encontrado nesta planilha.")
        print("         Se voce esperava dados novos, confira se importou o")
        print("         arquivo ATUALIZADO (veja a data acima).")
    print("  gestores :", db.query(models.Gestor).count())
    print("  vagas    :", db.query(models.Vaga).count())
    print("  candidatos:", db.query(models.Candidato).count())
    print("  ciclos   :", db.query(models.CicloVaga).count())
    db.close()


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--refazer"]
    refazer = "--refazer" in sys.argv
    caminho = args[0] if args else "Automacao_RH_v17.xlsx"
    importar(caminho, refazer=refazer)
