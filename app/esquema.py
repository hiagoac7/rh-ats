"""
Ajuste leve do esquema no SQLite.

Cria as tabelas e adiciona colunas novas em bancos que ja existem,
sem apagar dados. E chamado tanto pela API (main.py) quanto pelos
scripts (importar_planilha.py), para que qualquer um deles funcione
mesmo que o outro ainda nao tenha rodado.

No PostgreSQL o esquema e gerido pelo Alembic (alembic upgrade head).
"""
from .database import Base, engine, DATABASE_URL
from . import models

COLUNAS_NOVAS = {
    "config_email": [
        ("avisar_ti", "BOOLEAN DEFAULT 1"),
        ("email_ti", "VARCHAR(200)"),
    ],
    "usuarios": [
        ("extra_perms", "TEXT DEFAULT '[]'"),
        ("denied_perms", "TEXT DEFAULT '[]'"),
        ("foto", "TEXT"),
        ("preferencias", "TEXT"),
        ("senha_alterada_em", "DATETIME"),
    ],
    "candidatos": [
        ("banco_talentos", "BOOLEAN DEFAULT 0"),
        ("hora_1a_etapa", "VARCHAR(10)"),
        ("hora_2a_etapa", "VARCHAR(10)"),
        ("linha", "VARCHAR(60)"),
        ("consulta", "VARCHAR(20)"),
        ("chek", "VARCHAR(20)"),
        ("reagendado", "VARCHAR(40)"),
        ("reagendamento", "VARCHAR(40)"),
        ("extras", "TEXT"),
        ("versao", "INTEGER DEFAULT 1"),
    ],
    "vagas": [
        ("linha", "VARCHAR(60)"),
        ("rank", "INTEGER"),
        ("cargo_padrao", "VARCHAR(160)"),
        ("motivo", "VARCHAR(30)"),
        ("extras", "TEXT"),
        ("versao", "INTEGER DEFAULT 1"),
    ],
}


def garantir():
    """
    Prepara o esquema do banco.

    SQLite (uso local): cria as tabelas e adiciona colunas novas na hora,
    para o sistema funcionar sem passo extra.

    PostgreSQL (producao): NAO mexe no esquema. Quem manda e o Alembic
    (`alembic upgrade head`), que roda antes do sistema subir. Deixar os
    dois criando tabelas faria o controle de versao do banco se perder.
    """
    if not DATABASE_URL.startswith("sqlite"):
        return
    Base.metadata.create_all(bind=engine)
    with engine.begin() as con:
        existentes = {r[0] for r in con.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        for tabela, colunas in COLUNAS_NOVAS.items():
            if tabela not in existentes:
                continue
            atuais = {r[1] for r in con.exec_driver_sql(f"PRAGMA table_info({tabela})")}
            for coluna, tipo in colunas:
                if coluna not in atuais:
                    con.exec_driver_sql(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}")


def limpar_mudancas():
    """Remove avisos antigos — eles so servem para atualizar as telas."""
    from .database import SessionLocal
    from . import eventos
    db = SessionLocal()
    try:
        eventos.limpar_antigas(db)
    except Exception:
        db.rollback()
    finally:
        db.close()


def semear_listas():
    """Cria as listas padrao na primeira execucao."""
    from .database import SessionLocal
    from .listas_padrao import LISTAS_PADRAO
    db = SessionLocal()
    try:
        if db.query(models.Lista).count() == 0:
            for tipo, valores in LISTAS_PADRAO.items():
                for i, v in enumerate(valores):
                    db.add(models.Lista(tipo=tipo, valor=v, ordem=i, ativo=True))
            db.commit()
    finally:
        db.close()


def sincronizar_acessos():
    """Gera os pedidos de acesso que faltam para quem ja esta aprovado."""
    from .database import SessionLocal
    from .routers.acessos import sincronizar_aprovados
    db = SessionLocal()
    try:
        sincronizar_aprovados(db)
    except Exception:
        db.rollback()
    finally:
        db.close()


def preparar():
    """Deixa o banco pronto para uso (esquema + listas padrao + acessos)."""
    garantir()
    semear_listas()
    sincronizar_acessos()
    limpar_mudancas()
