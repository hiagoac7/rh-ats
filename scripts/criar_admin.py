"""
Cria (ou atualiza) um usuário administrador com perfil RH.

Uso:
    python -m scripts.criar_admin "Vanessa RH" rh@tlmequipamentos.com.br SenhaForte123
Se os argumentos forem omitidos, usa valores padrão (TROQUE a senha depois!).
"""
import sys
sys.path.insert(0, ".")
from app.database import SessionLocal
from app.esquema import preparar
from app import models, security


def criar_admin(nome: str, email: str, senha: str, perfil: str = "RH"):
    preparar()
    try:
        perfil_val = models.Perfil(perfil.upper()).value
    except ValueError:
        print("Perfil invalido:", perfil, "-> use RH, TI, GESTOR ou DIRETORIA")
        return
    db = SessionLocal()
    user = db.query(models.Usuario).filter_by(email=email).first()
    if user:
        user.senha_hash = security.hash_password(senha)
        user.perfil = perfil_val
        user.ativo = True
        acao = "atualizado"
    else:
        user = models.Usuario(
            nome=nome,
            email=email,
            senha_hash=security.hash_password(senha),
            perfil=perfil_val,
        )
        db.add(user)
        acao = "criado"
    db.commit()
    print(f"Usuário {acao}: {email} (perfil {perfil})")
    db.close()


if __name__ == "__main__":
    nome  = sys.argv[1] if len(sys.argv) > 1 else "Admin RH"
    email = sys.argv[2] if len(sys.argv) > 2 else "rh@tlmequipamentos.com.br"
    senha = sys.argv[3] if len(sys.argv) > 3 else "trocar-esta-senha"
    perfil= sys.argv[4] if len(sys.argv) > 4 else "RH"
    criar_admin(nome, email, senha, perfil)
