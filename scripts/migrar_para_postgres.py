"""
Move todos os dados do SQLite para o PostgreSQL.

Como usar:
  1) Crie o banco no PostgreSQL (ex.: rh_ats)
  2) Rode as migrations no destino:
       set DATABASE_URL=postgresql+psycopg://usuario:senha@servidor:5432/rh_ats
       alembic upgrade head
  3) Rode este script:
       python -m scripts.migrar_para_postgres

O SQLite nao e alterado — ele continua intacto como copia de seguranca.
"""
import os
import sys

sys.path.insert(0, ".")

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from app import models
from app.database import Base

ORIGEM = os.getenv("ORIGEM_URL", "sqlite:///./rh_ats.db")
DESTINO = os.getenv("DATABASE_URL", "")

TABELAS = [
    models.Gestor, models.Vaga, models.Candidato, models.CicloVaga,
    models.Usuario, models.Auditoria, models.Anotacao, models.Canal,
    models.Candidatura, models.Lista, models.MapaCargoGestor,
    models.CampoPersonalizado, models.ConfigEmail, models.ModeloMensagem,
    models.EnvioEmail, models.Requisicao, models.AcessoTI,
]


def colunas(modelo):
    return [c.name for c in modelo.__table__.columns]


def main():
    if not DESTINO or DESTINO.startswith("sqlite"):
        print("ERRO: defina DATABASE_URL apontando para o PostgreSQL.")
        print('  Exemplo: postgresql+psycopg://usuario:senha@servidor:5432/rh_ats')
        sys.exit(1)

    print(f"Origem : {ORIGEM}")
    print(f"Destino: {DESTINO.split('@')[-1]}")
    print()

    eo = create_engine(ORIGEM)
    ed = create_engine(DESTINO)
    So, Sd = sessionmaker(bind=eo), sessionmaker(bind=ed)
    origem, destino = So(), Sd()

    from sqlalchemy import inspect
    if "candidatos" not in inspect(ed).get_table_names():
        print("ERRO: as tabelas nao existem no destino.")
        print("      Rode antes:  alembic upgrade head")
        sys.exit(1)

    total = 0
    for modelo in TABELAS:
        nome = modelo.__tablename__
        try:
            registros = origem.scalars(select(modelo)).all()
        except Exception as e:
            print(f"  {nome:24} pulada ({type(e).__name__})")
            continue

        ja_tem = destino.query(modelo).count()
        if ja_tem:
            print(f"  {nome:24} destino ja tem {ja_tem} registro(s) — pulando")
            continue

        cols = colunas(modelo)
        novos = 0
        for r in registros:
            dados = {c: getattr(r, c) for c in cols}
            destino.add(modelo(**dados))
            novos += 1
        destino.commit()
        print(f"  {nome:24} {novos} registro(s) copiado(s)")
        total += novos

    with ed.connect() as con:
        for modelo in TABELAS:
            t = modelo.__tablename__
            try:
                con.execute(text(
                    f"SELECT setval(pg_get_serial_sequence('{t}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {t}), 1))"))
            except Exception:
                pass
        con.commit()

    origem.close(); destino.close()
    print(f"\nConcluido: {total} registro(s) migrado(s).")
    print("O arquivo rh_ats.db continua intacto como copia de seguranca.")


if __name__ == "__main__":
    main()
