"""Dependencies de autenticação e autorização."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from .database import get_db
from . import models, security

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.Usuario:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security.decode_access_token(token)
    except security.TokenInvalido:
        raise cred_exc
    email = payload.get("sub")
    user = db.scalar(select(models.Usuario).where(models.Usuario.email == email))
    if user is None or not user.ativo:
        raise cred_exc

    if user.senha_alterada_em:
        emitido_em = payload.get("iat")
        if emitido_em is None:
            raise cred_exc
        from datetime import timezone as _tz
        trocada = user.senha_alterada_em.replace(tzinfo=_tz.utc).timestamp()
        if emitido_em + 60 < trocada:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sua senha foi alterada. Entre novamente.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    return user


def require_roles(*perfis: models.Perfil):
    """Fábrica de dependency que exige um dos perfis informados."""
    perfis_set = {p.value for p in perfis}

    def checker(user: models.Usuario = Depends(get_current_user)) -> models.Usuario:
        if user.perfil not in perfis_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Perfil necessário: {', '.join(sorted(perfis_set))}",
            )
        return user

    return checker


def require_perm(*perms: str):
    """Exige que o usuário tenha PELO MENOS UMA das permissões informadas."""
    alvo = set(perms)

    def checker(user: models.Usuario = Depends(get_current_user)) -> models.Usuario:
        if not (alvo & set(user.permissoes)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para esta ação: " + ", ".join(sorted(alvo)),
            )
        return user

    return checker


def usuario_do_token(token: str | None, db: Session) -> models.Usuario:
    """
    Valida um token recebido fora do cabecalho.

    Usado apenas pelo canal de tempo real: o navegador nao consegue enviar
    cabecalhos nesse tipo de conexao, entao o token vai na propria URL.
    """
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise cred_exc
    try:
        payload = security.decode_access_token(token)
    except security.TokenInvalido:
        raise cred_exc
    user = db.scalar(select(models.Usuario).where(models.Usuario.email == payload.get("sub")))
    if user is None or not user.ativo:
        raise cred_exc
    return user
