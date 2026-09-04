"""
Configuracao do banco de dados.

Por padrao usa SQLite (arquivo rh_ats.db) para rodar sem instalar nada.
Para producao, troque a URL por PostgreSQL, ex.:
    DATABASE_URL=postgresql+psycopg://usuario:senha@localhost:5432/rh_ats
e instale o driver: pip install "psycopg[binary]"
"""
import os
from sqlalchemy import create_engine

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./rh_ats.db")

EH_SQLITE = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if EH_SQLITE else {}

_extra = {} if EH_SQLITE else {
    "pool_size": int(os.getenv("POOL_TAMANHO", "20")),
    "max_overflow": int(os.getenv("POOL_FOLGA", "20")),
    "pool_recycle": 1800,
    "pool_pre_ping": True,
}

if EH_SQLITE:
    connect_args["timeout"] = 30

engine = create_engine(DATABASE_URL, connect_args=connect_args, **_extra)

if EH_SQLITE:
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def _ajustar_sqlite(conexao, _registro):
        """
        Ajustes aplicados a cada conexao nova.

        WAL (write-ahead log) e o que permite VARIAS pessoas lendo enquanto uma
        escreve. No modo padrao do SQLite, uma unica escrita do RH bloqueia todo
        mundo — e o canal de tempo real consulta o banco a cada 1,5 segundos por
        pessoa conectada, entao a chance de colisao e alta.

        busy_timeout: em vez de falhar na hora, espera ate 30s pela vez.
        synchronous=NORMAL: seguro com WAL e bem mais rapido que FULL.
        """
        cur = conexao.cursor()
        try:
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA busy_timeout=30000")
            cur.execute("PRAGMA synchronous=NORMAL")
            cur.execute("PRAGMA foreign_keys=ON")
        finally:
            cur.close()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency do FastAPI: abre uma sessao por request e fecha no fim."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
