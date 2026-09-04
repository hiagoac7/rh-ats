"""
Segurança: hash de senha (PBKDF2) e tokens JWT (HS256).

Implementado só com a biblioteca padrão do Python — não precisa instalar nada.
Se preferir bibliotecas consagradas em produção, dá para trocar por:
    passlib[bcrypt]  (hash)  e  pyjwt  (tokens)
sem mudar o resto do código, contanto que a interface (funções abaixo) seja mantida.
"""
import os
import hmac
import json
import base64
import hashlib
from datetime import datetime, timezone, timedelta

def _chave_secreta() -> str:
    """
    Chave usada para assinar os tokens de login.

    Ordem: variavel de ambiente SECRET_KEY (recomendado em producao) ->
    arquivo .chave_secreta gerado automaticamente na primeira execucao.
    Assim cada instalacao tem uma chave unica, sem depender de configuracao
    manual — e ninguem consegue forjar um login com a chave do codigo.
    """
    da_variavel = os.getenv("SECRET_KEY")
    if da_variavel:
        return da_variavel

    if os.getenv("DATABASE_URL", "").startswith("postgres"):
        raise RuntimeError(
            "SECRET_KEY nao definida. Em producao ela e obrigatoria — "
            "defina no arquivo .env. Gere uma com: openssl rand -base64 48")
    caminho = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           ".chave_secreta")
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as fp:
            chave = fp.read().strip()
            if chave:
                return chave
    import secrets
    chave = secrets.token_urlsafe(48)
    try:
        with open(caminho, "w", encoding="utf-8") as fp:
            fp.write(chave)
        if os.name != "nt":
            os.chmod(caminho, 0o600)
    except OSError:
        pass
    return chave


SECRET_KEY = _chave_secreta()
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MIN", "480"))
_PBKDF2_ROUNDS = 200_000


def agora_utc() -> datetime:
    """
    Instante atual em UTC, SEM fuso colado (naive).

    Existe para um caso especifico: comparar "senha_alterada_em" com o "iat"
    do token de login. O resto do sistema grava datas com datetime.now(), que
    e hora local (America/Sao_Paulo); o JWT trabalha em UTC. Misturar os dois
    daria 3 horas de diferenca e derrubaria (ou deixaria passar) sessoes na
    hora errada. Toda gravacao de senha_alterada_em usa esta funcao.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def hash_password(senha: str) -> str:
    """Gera hash salgado: pbkdf2_sha256$rounds$salt$hash."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt, _PBKDF2_ROUNDS)
    return f"pbkdf2_sha256${_PBKDF2_ROUNDS}${salt.hex()}${dk.hex()}"


def verify_password(senha: str, armazenado: str) -> bool:
    try:
        algo, rounds, salt_hex, hash_hex = armazenado.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", senha.encode(), bytes.fromhex(salt_hex), int(rounds))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def create_access_token(sub: str, role: str, minutos: int | None = None) -> str:
    agora = datetime.now(timezone.utc)
    exp = agora + timedelta(minutes=minutos or ACCESS_TOKEN_EXPIRE_MINUTES)
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": sub, "role": role,
               "iat": int(agora.timestamp()), "exp": int(exp.timestamp())}
    seg = _b64(json.dumps(header, separators=(",", ":")).encode()) + "." + \
          _b64(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(SECRET_KEY.encode(), seg.encode(), hashlib.sha256).digest()
    return seg + "." + _b64(sig)


class TokenInvalido(Exception):
    pass


def decode_access_token(token: str) -> dict:
    try:
        seg_h, seg_p, seg_s = token.split(".")
    except ValueError:
        raise TokenInvalido("formato inválido")
    seg = f"{seg_h}.{seg_p}"
    esperado = hmac.new(SECRET_KEY.encode(), seg.encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(_unb64(seg_s), esperado):
        raise TokenInvalido("assinatura inválida")
    payload = json.loads(_unb64(seg_p))
    if payload.get("exp", 0) < int(datetime.now(timezone.utc).timestamp()):
        raise TokenInvalido("token expirado")
    return payload
