"""Schemas Pydantic: validam entrada e formatam saida da API."""
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict


class GestorBase(BaseModel):
    nome: str
    email: str | None = None

class GestorCreate(GestorBase):
    pass

class GestorUpdate(BaseModel):
    nome: str | None = None
    email: str | None = None

class GestorOut(GestorBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class VagaBase(BaseModel):
    codigo: str | None = None
    cargo: str
    cargo_padrao: str | None = None
    nivel: str | None = None
    qtde: int = 1
    tipo: str | None = None
    motivo: str | None = None
    salario: float | None = None
    area: str | None = None
    linha: str | None = None
    rank: int | None = None
    extras: dict | None = None
    status: str | None = None
    data_abertura: date | None = None
    previsao_inicio: date | None = None
    data_fechamento: date | None = None
    observacoes: str | None = None
    gestor_id: int | None = None

class VagaCreate(VagaBase):
    confirmar_duplicado: bool = False

class VagaUpdate(BaseModel):
    confirmar_pendencias: bool = False
    confirmar_duplicado: bool = False
    versao: int | None = None
    cargo: str | None = None
    cargo_padrao: str | None = None
    nivel: str | None = None
    qtde: int | None = None
    tipo: str | None = None
    motivo: str | None = None
    salario: float | None = None
    area: str | None = None
    linha: str | None = None
    rank: int | None = None
    extras: dict | None = None
    status: str | None = None
    data_abertura: date | None = None
    previsao_inicio: date | None = None
    data_fechamento: date | None = None
    observacoes: str | None = None
    gestor_id: int | None = None

class VagaOut(VagaBase):
    id: int
    versao: int = 1
    model_config = ConfigDict(from_attributes=True)


class CandidatoBase(BaseModel):
    nome: str
    cargo: str | None = None
    contato: str | None = None
    cpf: str | None = None
    email: str | None = None
    origem: str | None = None
    contato_inicial: date | None = None
    data_1a_etapa: datetime | None = None
    hora_1a_etapa: str | None = None
    data_2a_etapa: datetime | None = None
    hora_2a_etapa: str | None = None
    data_aprovacao: date | None = None
    parecer: str | None = None
    disc: str | None = None
    consulta: str | None = None
    chek: str | None = None
    reagendado: str | None = None
    reagendamento: str | None = None
    status: str | None = None
    etapa_atual: str | None = None
    gestor_nome: str | None = None
    devolutiva: str | None = None
    observacoes: str | None = None
    linha: str | None = None
    banco_talentos: bool = False
    extras: dict | None = None
    vaga_id: int | None = None

class CandidatoCreate(CandidatoBase):
    confirmar_pendencias: bool = False
    confirmar_duplicado: bool = False

class CandidatoUpdate(BaseModel):
    confirmar_pendencias: bool = False
    confirmar_duplicado: bool = False
    versao: int | None = None
    nome: str | None = None
    cargo: str | None = None
    contato: str | None = None
    cpf: str | None = None
    email: str | None = None
    origem: str | None = None
    contato_inicial: date | None = None
    data_1a_etapa: datetime | None = None
    hora_1a_etapa: str | None = None
    data_2a_etapa: datetime | None = None
    hora_2a_etapa: str | None = None
    data_aprovacao: date | None = None
    parecer: str | None = None
    disc: str | None = None
    consulta: str | None = None
    chek: str | None = None
    reagendado: str | None = None
    reagendamento: str | None = None
    status: str | None = None
    etapa_atual: str | None = None
    gestor_nome: str | None = None
    devolutiva: str | None = None
    observacoes: str | None = None
    linha: str | None = None
    banco_talentos: bool | None = None
    extras: dict | None = None
    vaga_id: int | None = None

class CandidatoOut(CandidatoBase):
    id: int
    versao: int = 1
    dias_parado: int | None = None
    model_config = ConfigDict(from_attributes=True)


class CicloOut(BaseModel):
    id: int
    vaga_id: int
    linha: str | None = None
    data_abertura: date | None = None
    data_fechamento: date | None = None
    candidatos: int | None = None
    aprovados: int | None = None
    status: str | None = None
    observacoes: str | None = None
    model_config = ConfigDict(from_attributes=True)


class PainelOut(BaseModel):
    candidatos_cadastrados: int
    em_processo: int
    aprovados: int
    taxa_aprovacao: float
    vagas_em_aberto: int
    funil: dict[str, int]

class FilaItem(BaseModel):
    id: int
    candidato: str
    cargo: str | None
    gestor: str | None
    data_2a_etapa: datetime | None
    hora_2a_etapa: str | None = None
    dias_parado: int | None
    situacao: str
    contato: str | None
    email: str | None


from .models import Perfil

class UsuarioCreate(BaseModel):
    nome: str
    email: str
    senha: str
    perfil: Perfil = Perfil.RH

class UsuarioOut(BaseModel):
    id: int
    nome: str
    email: str
    perfil: Perfil
    ativo: bool
    extra_perms: list[str] = []
    denied_perms: list[str] = []
    permissoes: list[str] = []
    model_config = ConfigDict(from_attributes=True)

class UsuarioUpdate(BaseModel):
    nome: str | None = None
    perfil: Perfil | None = None
    ativo: bool | None = None
    senha: str | None = None
    extra_perms: list[str] | None = None
    denied_perms: list[str] | None = None

class LoginIn(BaseModel):
    email: str
    senha: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    perfil: Perfil
    nome: str
    permissoes: list[str] = []



class DefinirSenhaIn(BaseModel):
    senha: str



class AvaliacaoCreate(BaseModel):
    etapa: str = "RH"
    notas: dict[str, int] = {}
    recomendacao: str | None = None
    comentario: str | None = None


class AvaliacaoOut(BaseModel):
    id: int
    candidato_id: int
    etapa: str
    autor: str | None = None
    criado_em: datetime | None = None
    notas: dict | None = None
    recomendacao: str | None = None
    comentario: str | None = None
    media: float | None = None
    model_config = ConfigDict(from_attributes=True)


class EventoHistorico(BaseModel):
    quando: datetime | None = None
    tipo: str
    titulo: str
    detalhe: str | None = None
    quem: str | None = None


class MeOut(BaseModel):
    id: int
    nome: str
    email: str
    perfil: Perfil
    foto: str | None = None
    preferencias: dict | None = None
    permissoes: list[str] = []
    model_config = ConfigDict(from_attributes=True)

class CatalogoPermissoes(BaseModel):
    permissoes: dict[str, str]
    grupos: dict[str, list[str]]
    papeis: dict[str, list[str]]


class AuditoriaOut(BaseModel):
    id: int
    criado_em: datetime
    ator_nome: str | None = None
    acao: str
    entidade: str | None = None
    entidade_id: str | None = None
    detalhes: dict | None = None
    model_config = ConfigDict(from_attributes=True)


class AnotacaoCreate(BaseModel):
    texto: str

class AnotacaoOut(BaseModel):
    id: int
    candidato_id: int
    autor: str | None = None
    texto: str
    criado_em: datetime
    model_config = ConfigDict(from_attributes=True)


class CanalBase(BaseModel):
    nome: str
    link: str | None = None
    responsavel: str | None = None
    login: str | None = None
    ativo: bool = True
    observacoes: str | None = None

class CanalCreate(CanalBase):
    pass

class CanalUpdate(BaseModel):
    nome: str | None = None
    link: str | None = None
    responsavel: str | None = None
    login: str | None = None
    ativo: bool | None = None
    observacoes: str | None = None

class CanalOut(CanalBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class CandidaturaCreate(BaseModel):
    canal_id: int
    vaga_id: int | None = None
    quantidade: int = 0
    data: date | None = None
    observacoes: str | None = None

class CandidaturaOut(CandidaturaCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ListaCreate(BaseModel):
    tipo: str
    valor: str
    ordem: int = 0
    ativo: bool = True

class ListaUpdate(BaseModel):
    valor: str | None = None
    ordem: int | None = None
    ativo: bool | None = None

class ListaOut(ListaCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class MapaCreate(BaseModel):
    cargo: str
    gestor: str

class MapaOut(MapaCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class PerfilUpdate(BaseModel):
    """O próprio usuário editando seus dados."""
    nome: str | None = None
    foto: str | None = None
    preferencias: dict | None = None
    senha_atual: str | None = None
    senha_nova: str | None = None


class CampoCreate(BaseModel):
    entidade: str
    chave: str
    rotulo: str
    tipo: str = "texto"
    opcoes: list[str] | None = None
    ordem: int = 0
    ativo: bool = True

class CampoUpdate(BaseModel):
    rotulo: str | None = None
    tipo: str | None = None
    opcoes: list[str] | None = None
    ordem: int | None = None
    ativo: bool | None = None

class CampoOut(CampoCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ConfigEmailIn(BaseModel):
    servidor: str | None = None
    porta: int = 587
    usuario: str | None = None
    senha: str | None = None
    remetente: str | None = None
    nome_remetente: str | None = None
    ativo: bool = False
    avisar_gestor: bool = True
    avisar_ti: bool = True
    email_ti: str | None = None
    lembrete_entrevista: bool = True
    horas_antes: int = 24

class ConfigEmailOut(BaseModel):
    id: int
    servidor: str | None = None
    porta: int
    usuario: str | None = None
    remetente: str | None = None
    nome_remetente: str | None = None
    ativo: bool
    avisar_gestor: bool
    avisar_ti: bool = True
    email_ti: str | None = None
    lembrete_entrevista: bool
    horas_antes: int
    tem_senha: bool = False
    model_config = ConfigDict(from_attributes=True)


class ModeloIn(BaseModel):
    nome: str
    canal: str = "email"
    gatilho: str | None = None
    assunto: str | None = None
    corpo: str
    ativo: bool = True

class ModeloUpdate(BaseModel):
    nome: str | None = None
    canal: str | None = None
    gatilho: str | None = None
    assunto: str | None = None
    corpo: str | None = None
    ativo: bool | None = None

class ModeloOut(ModeloIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


class EnviarIn(BaseModel):
    candidato_id: int
    modelo_id: int | None = None
    assunto: str | None = None
    corpo: str | None = None

class PreviaOut(BaseModel):
    para: str | None = None
    assunto: str | None = None
    corpo: str
    telefone: str | None = None
    link_whatsapp: str | None = None


class EnvioOut(BaseModel):
    id: int
    criado_em: datetime
    para: str
    assunto: str | None = None
    tipo: str | None = None
    sucesso: bool
    erro: str | None = None
    model_config = ConfigDict(from_attributes=True)


class RequisicaoIn(BaseModel):
    cargo: str
    nivel: str | None = None
    qtde: int = 1
    tipo: str | None = None
    motivo: str | None = None
    substituindo: str | None = None
    area: str | None = None
    linha: str | None = None
    salario: float | None = None
    previsao_inicio: date | None = None
    justificativa: str | None = None
    gestor_id: int | None = None

class RequisicaoDecisao(BaseModel):
    aprovar: bool
    observacao_decisao: str | None = None

class RequisicaoOut(RequisicaoIn):
    id: int
    criado_em: datetime
    solicitante: str | None = None
    status: str
    decidido_por: str | None = None
    decidido_em: datetime | None = None
    observacao_decisao: str | None = None
    vaga_id: int | None = None
    model_config = ConfigDict(from_attributes=True)


class AcessoUpdate(BaseModel):
    status: str | None = None
    itens: dict | None = None
    observacoes: str | None = None

class AcessoOut(BaseModel):
    id: int
    candidato_id: int
    criado_em: datetime
    status: str
    itens: dict | None = None
    observacoes: str | None = None
    responsavel: str | None = None
    concluido_em: datetime | None = None
    candidato: str | None = None
    cargo: str | None = None
    area: str | None = None
    gestor: str | None = None
    email: str | None = None
    contato: str | None = None
    data_aprovacao: date | None = None
    previsao_inicio: date | None = None
    model_config = ConfigDict(from_attributes=True)


class PendenciaOut(BaseModel):
    campo: str | None = None
    rotulo: str
    porque: str
    nivel: str

class PendenciasResposta(BaseModel):
    pendencias: list[PendenciaOut] = []
    bloqueia: bool = False
