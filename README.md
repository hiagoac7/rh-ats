# ATS TLM — Sistema interno de Recrutamento & Seleção

API em **Python + FastAPI** que substitui a planilha `Automacao_RH`.
Passo a passo para rodar do zero.

## 1. Pré-requisitos
- Python 3.11+ instalado.

## 2. Instalar
```bash
cd rh_ats
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
```

## 2.1. Trazer as bibliotecas para dentro (faça isto uma vez)

O front-end usa React, Babel, Tailwind e Chart.js. Por padrão eles seriam
baixados da internet **a cada abertura de página** — o que significa tela
branca sempre que a rede da empresa bloquear `unpkg.com`, ou o CDN sair do ar.

```bash
python -m scripts.baixar_bibliotecas     # Windows: baixar_bibliotecas.bat
```

Isso grava os arquivos em `app/static/vendor/` e o sistema passa a servi-los
sozinho. Precisa de internet **só nesse momento** — depois a pasta pode ser
copiada para máquinas sem acesso externo.

Se você pular este passo o sistema continua funcionando: cada `<script>` tem
uma linha de reserva que cai para a internet automaticamente. Você só fica
dependente de rede externa.

## 3. Importar os dados da planilha
Coloque o arquivo `Automacao_RH_v17.xlsx` na pasta `rh_ats/` e rode:
```bash
python -m scripts.importar_planilha Automacao_RH_v17.xlsx
```
Isso cria o banco `rh_ats.db` (SQLite) e carrega vagas, candidatos, ciclos e gestores.

## 4. Subir a API
```bash
uvicorn app.main:app --reload
```
Abra a documentação interativa (testa tudo pelo navegador):
- http://localhost:8000/docs

## 5. Endpoints principais
| Método | Rota | O que faz |
|---|---|---|
| GET  | `/vagas` | lista vagas (filtros: `status`, `gestor_id`) |
| POST | `/vagas` | cria vaga |
| PATCH| `/vagas/{id}` | atualiza vaga |
| GET  | `/candidatos` | lista/filtra (`vaga_id`, `status`, `etapa`) |
| POST | `/candidatos` | cadastra candidato |
| PATCH| `/candidatos/{id}` | atualiza parecer/etapa/status |
| GET  | `/ciclos` | ciclos das vagas perenes (Vendedor/SDR) |
| GET  | `/painel` | indicadores (calculado) |
| GET  | `/fila-gestao` | candidatos aguardando parecer + dias parado |

## 6. Ir para PostgreSQL (produção)
```bash
pip install "psycopg[binary]"
export DATABASE_URL="postgresql+psycopg://usuario:senha@localhost:5432/rh_ats"
```
Nenhuma mudança de código é necessária — a mesma app roda em SQLite ou Postgres.

## Estrutura
```
rh_ats/
├── requirements.txt
├── app/
│   ├── main.py          # cria a app e registra as rotas
│   ├── database.py      # conexão (SQLite/Postgres)
│   ├── models.py        # tabelas (SQLAlchemy)
│   ├── schemas.py       # validação de entrada/saída (Pydantic)
│   └── routers/         # endpoints por área
│       ├── vagas.py
│       ├── candidatos.py
│       ├── ciclos.py
│       ├── painel.py    # indicadores calculados
│       └── fila.py      # fila de parecer da gestão
└── scripts/
    └── importar_planilha.py
```

---

## 7. Autenticação e perfis

O sistema usa **login com token JWT** e três perfis de acesso:

| Perfil | Pode fazer |
|---|---|
| **RH** | tudo: cadastrar/editar vagas e candidatos, ver painel/fila, **gerenciar usuários** |
| **GESTOR** | dar parecer nos candidatos, ver vagas, painel e a fila de parecer |
| **DIRETORIA** | somente leitura: vagas, candidatos, painel |

### Criar o primeiro usuário (admin RH)
```bash
python -m scripts.criar_admin "Vanessa RH" rh@tlmequipamentos.com.br SuaSenhaForte
```

### Fazer login
`POST /auth/login` (formato `application/x-www-form-urlencoded`):
- `username` = e-mail do usuário
- `password` = senha

Resposta traz `access_token`. Nas demais chamadas, envie o header:
```
Authorization: Bearer <access_token>
```
No `/docs`, clique em **Authorize** e faça login por lá — todas as rotas passam a ser testáveis autenticado.

### Rotas de auth
| Método | Rota | Perfil |
|---|---|---|
| POST | `/auth/login` | público |
| GET  | `/auth/me` | autenticado |
| GET  | `/auth/usuarios` | RH |
| POST | `/auth/usuarios` | RH |

### Segurança — o que configurar em produção
Defina variáveis de ambiente (NÃO use os padrões em produção):
```bash
export SECRET_KEY="uma-chave-longa-e-aleatoria"   # assina os tokens
export TOKEN_EXPIRE_MIN=480                        # validade do token (min)
```
As senhas são guardadas com hash PBKDF2-SHA256 (salgado). Tokens e hash usam só a
biblioteca padrão do Python — se preferir, dá para trocar por `pyjwt` + `passlib[bcrypt]`
mantendo a mesma interface em `app/security.py`.

---

## 8. Banco em produção: PostgreSQL + migrations (Alembic)

O sistema nasce em **SQLite** (um arquivo, zero instalação) e migra para **PostgreSQL**
sem trocar código — só configuração. As mudanças de estrutura do banco passam a ser
**versionadas com Alembic**, para o banco evoluir com segurança conforme o sistema cresce.

### Por que isso importa
- **SQLite**: ótimo para testar, mas não foi feito para várias pessoas gravando ao mesmo tempo.
- **PostgreSQL**: aguenta acesso simultâneo, é o padrão para sistemas alimentados todo dia.
- **Alembic**: quando você adicionar um campo (ex.: "telefone 2" no candidato) ou uma tabela,
  gera um "passo de migração" que aplica a mudança **sem apagar os dados existentes**.

### Passo a passo para ir ao PostgreSQL
1. Instale o PostgreSQL e crie um banco (ex.: `rh_ats`) e um usuário.
2. Copie `.env.example` para `.env` e ajuste a linha:
   ```
   DATABASE_URL=postgresql+psycopg://rh_user:senha_forte@localhost:5432/rh_ats
   SECRET_KEY=uma-chave-longa-e-aleatoria
   ```
3. Crie a estrutura do banco (dois cliques em **`migrar.bat`**, ou):
   ```
   alembic upgrade head
   ```
4. Carregue os dados da planilha (uma vez) e crie os logins:
   ```
   python -m scripts.importar_planilha Automacao_RH_v17.xlsx
   python -m scripts.criar_admin "Seu Nome" seu@email.com SuaSenha TI
   ```
5. Suba o sistema normalmente (`iniciar.bat`).

### O fluxo do dia a dia quando mudar o banco
Sempre que você alterar os models (adicionar/mudar um campo), rode:
```
alembic revision --autogenerate -m "descricao da mudanca"
alembic upgrade head
```
- O primeiro comando **gera** o passo de migração comparando os models com o banco.
- O segundo **aplica** a mudança. Os dados existentes são preservados.

> No SQLite, o sistema ainda cria as tabelas sozinho ao iniciar (praticidade no
> desenvolvimento). No PostgreSQL, quem cria e evolui o schema é o Alembic.

---

## 9. O sistema é autossuficiente (a planilha pode ser aposentada)

Tudo que a planilha fazia é feito pelo sistema:

| Na planilha | No sistema |
|---|---|
| Abas CANDIDATOS / VAGAS | Telas de Candidatos e Vagas (criar, editar, excluir) |
| Aba LISTAS | **Configurações** — cargos, origens, áreas, níveis, etapas... editáveis |
| Aba PAINEL | **Relatórios** (com filtro de período) |
| Aba FILA GESTÃO | **Fila Gestão** |
| Abas CICLOS | Histórico de aberturas dentro da vaga + botão **Reabrir vaga** |
| Aba DIVULGAÇÃO | **Divulgação** (sem senhas — use um gerenciador de senhas) |
| O arquivo .xlsx em si | **Exportar Excel** + **backup.bat** |

### Configurações (a nova aba LISTAS)
Em **Configurações** você adiciona/renomeia/reordena os valores dos menus.
Ao renomear um item de *Etapas* ou *Status do candidato*, o sistema atualiza
automaticamente os registros que usavam o nome antigo — nada fica órfão.
Desativar esconde o valor dos menus sem apagar o histórico.

### Exportar para Excel
Botão **Exportar Excel** na tela de Relatórios. Gera um .xlsx com as abas
CANDIDATOS, VAGAS, ANOTAÇÕES, GESTORES, DIVULGAÇÃO, CANDIDATURAS, LISTAS e USUÁRIOS.
Serve para conferência, envio à diretoria e para garantir que os dados nunca ficam presos.

### Backup (importante)
Os dados vivem no arquivo `rh_ats.db`. Faça backup com regularidade:

- **`backup.bat`** — dois cliques, salva uma cópia datada na pasta `backups\`.
- Feche o sistema antes de rodar, para copiar o banco sem uso.
- Guarde uma cópia fora do computador (nuvem, HD externo).

> Ao migrar para PostgreSQL (seção 8), o backup passa a ser feito pelo próprio
> servidor de banco (`pg_dump`), que é o caminho recomendado para uso em rede.
