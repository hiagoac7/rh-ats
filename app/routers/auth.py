from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user, require_perm
from ..permissions import PERMISSOES, GRUPOS, ROLE_PERMS
from .. import models, schemas, security, senha_service, email_service
from ..audit import registrar

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=schemas.Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login OAuth2 password flow. 'username' = e-mail do usuário."""
    user = db.scalar(select(models.Usuario).where(models.Usuario.email == form.username))
    if not user or not security.verify_password(form.password, user.senha_hash) or not user.ativo:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha inválidos")
    registrar(db, user, "login", "usuario", user.id); db.commit()
    token = security.create_access_token(sub=user.email, role=user.perfil)
    return schemas.Token(access_token=token, perfil=user.perfil, nome=user.nome,
                         permissoes=user.permissoes)


@router.get("/me", response_model=schemas.MeOut)
def eu(user: models.Usuario = Depends(get_current_user)):
    return user


@router.patch("/perfil", response_model=schemas.MeOut)
def atualizar_perfil(dados: schemas.PerfilUpdate, db: Session = Depends(get_db),
                     user: models.Usuario = Depends(get_current_user)):
    """O usuário edita os próprios dados: nome, foto, preferências e senha."""
    campos = dados.model_dump(exclude_unset=True)

    if campos.get("senha_nova"):
        if not campos.get("senha_atual"):
            raise HTTPException(400, "Informe a senha atual para trocar a senha")
        if not security.verify_password(campos["senha_atual"], user.senha_hash):
            raise HTTPException(400, "Senha atual incorreta")
        if len(campos["senha_nova"]) < 6:
            raise HTTPException(400, "A nova senha precisa ter pelo menos 6 caracteres")
        user.senha_hash = security.hash_password(campos["senha_nova"])

    if campos.get("nome"):
        user.nome = campos["nome"]
    if "foto" in campos:
        foto = campos["foto"]
        if foto and len(foto) > 2_000_000:
            raise HTTPException(400, "Imagem muito grande. Use uma foto menor que 1,5 MB.")
        user.foto = foto
    if campos.get("preferencias") is not None:
        user.preferencias = {**(user.preferencias or {}), **campos["preferencias"]}

    registrar(db, user, "editar_perfil", "usuario", user.id,
              {"campos": [k for k in campos if k not in ("senha_atual", "senha_nova", "foto")]})
    db.commit(); db.refresh(user)
    return user


@router.get("/catalogo-permissoes", response_model=schemas.CatalogoPermissoes)
def catalogo(_: models.Usuario = Depends(require_perm("usuarios.gerenciar"))):
    return schemas.CatalogoPermissoes(
        permissoes=PERMISSOES,
        grupos=GRUPOS,
        papeis={k: sorted(v) for k, v in ROLE_PERMS.items()},
    )


@router.get("/usuarios", response_model=list[schemas.UsuarioOut])
def listar_usuarios(db: Session = Depends(get_db),
                    _: models.Usuario = Depends(require_perm("usuarios.gerenciar"))):
    return db.scalars(select(models.Usuario)).all()


@router.post("/usuarios", response_model=schemas.UsuarioOut, status_code=201)
def criar_usuario(dados: schemas.UsuarioCreate, db: Session = Depends(get_db),
                  _: models.Usuario = Depends(require_perm("usuarios.gerenciar"))):
    if db.scalar(select(models.Usuario).where(models.Usuario.email == dados.email)):
        raise HTTPException(400, "E-mail já cadastrado")
    user = models.Usuario(
        nome=dados.nome, email=dados.email,
        senha_hash=security.hash_password(dados.senha),
        perfil=dados.perfil.value,
    )
    db.add(user); db.flush()
    registrar(db, _, "criar_usuario", "usuario", user.id,
              {"nome": user.nome, "email": user.email, "perfil": user.perfil})
    db.commit(); db.refresh(user)
    return user


@router.patch("/usuarios/{uid}", response_model=schemas.UsuarioOut)
def atualizar_usuario(uid: int, dados: schemas.UsuarioUpdate, db: Session = Depends(get_db),
                      user_atual: models.Usuario = Depends(require_perm("usuarios.gerenciar"))):
    u = db.get(models.Usuario, uid)
    if not u:
        raise HTTPException(404, "Usuário não encontrado")
    if u.id == user_atual.id and dados.ativo is False:
        raise HTTPException(400, "Você não pode desativar a si mesmo")
    campos = dados.model_dump(exclude_unset=True)
    if campos.get("senha"):
        u.senha_hash = security.hash_password(campos.pop("senha"))
        u.senha_alterada_em = security.agora_utc()
    else:
        campos.pop("senha", None)
    if campos.get("perfil"):
        u.perfil = models.Perfil(campos.pop("perfil")).value
    else:
        campos.pop("perfil", None)
    for k, v in campos.items():
        setattr(u, k, v)
    registrar(db, user_atual, "editar_usuario", "usuario", u.id, dados.model_dump(exclude_unset=True))
    db.commit(); db.refresh(u)
    return u




@router.post("/usuarios/{uid}/senha", status_code=200)
def ti_define_senha(uid: int, dados: schemas.DefinirSenhaIn, db: Session = Depends(get_db),
                    user_atual: models.Usuario = Depends(require_perm("usuarios.gerenciar"))):
    """
    O TI troca a senha de alguem na hora.

    Existe para o caso real: a pessoa perdeu o acesso, o e-mail dela nao
    funciona, e o trabalho nao pode parar. Em troca da praticidade:
      * fica registrado na auditoria QUEM trocou a senha de QUEM;
      * a pessoa e desconectada de todos os aparelhos na hora;
      * se der, ela recebe um aviso por e-mail de que a senha foi trocada —
        e nao um aviso opcional: e assim que ela percebe se alguem fez isso
        sem combinar com ela.
    """
    u = db.get(models.Usuario, uid)
    if not u:
        raise HTTPException(404, "Usuário não encontrado")
    problema = senha_service.problema_na_senha(dados.senha)
    if problema:
        raise HTTPException(400, problema)

    u.senha_hash = security.hash_password(dados.senha)
    u.senha_alterada_em = security.agora_utc()
    registrar(db, user_atual, "definiu_senha_de_usuario", "usuario", u.id,
              {"usuario": u.email})
    db.commit()

    aviso = None
    if u.email:
        ok, _ = email_service.enviar(
            db, u.email, "Sua senha do ATS foi alterada",
            f"Olá, {(u.nome or '').split(' ')[0]}.\n\n"
            f"O TI ({user_atual.nome}) definiu uma senha nova para o seu acesso ao "
            "sistema de Recrutamento e Seleção. Você foi desconectado de todos os "
            "aparelhos.\n\n"
            "Se você NÃO combinou isso com o TI, avise imediatamente.\n\n"
            "— Sistema ATS · TLM Equipamentos", tipo="senha")
        if not ok:
            aviso = "Senha trocada, mas não consegui avisar a pessoa por e-mail."

    return {"mensagem": f"Senha de {u.nome} alterada. Ela foi desconectada de todos os aparelhos.",
            "aviso": aviso}
