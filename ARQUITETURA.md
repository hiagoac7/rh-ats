# Arquitetura — ATS TLM

## 1. Visão geral
Sistema interno de Recrutamento & Seleção que substitui a planilha `Automacao_RH`.
A planilha continua sendo a fonte de carga inicial (via script de importação); depois,
os dados passam a viver no banco e são acessados/alterados pela API.

```
Planilha xlsx ──(importar_planilha.py)──▶ Banco (SQLite/Postgres)
                                              ▲
                            Front-end / integrações ──▶ API FastAPI
```

## 2. Stack
| Camada | Tecnologia | Motivo |
|---|---|---|
| Linguagem | Python 3.11+ | time de TI interno; fácil manter |
| API | FastAPI | docs automáticas (Swagger), rápido, validação nativa |
| ORM | SQLAlchemy 2 | modela as tabelas sem escrever SQL manual |
| Validação | Pydantic 2 | garante que entrada/saída estão corretas |
| Banco | SQLite (dev) → PostgreSQL (prod) | começa sem instalar nada, migra sem trocar código |
| Servidor | Uvicorn | roda a aplicação ASGI |

## 3. Modelo de dados
As abas da planilha viraram tabelas:

| Aba da planilha | Tabela | Observação |
|---|---|---|
| VAGAS | `vagas` | chave natural = `codigo` (V001…) |
| CANDIDATOS | `candidatos` | FK `vaga_id` → vagas |
| CICLOS VENDEDOR / SDR | `ciclos_vaga` | períodos de vagas perenes |
| LISTAS (cargo→gestor→e-mail) | `gestores` | alimenta e-mail para avisos |
| PAINEL | *(não é tabela)* | calculado em `/painel` |
| FILA GESTÃO | *(não é tabela)* | calculado em `/fila-gestao` |

Relações:
```
gestores 1──N vagas 1──N candidatos
                  1──N ciclos_vaga
```

### Por que PAINEL e FILA não são tabelas
Na planilha eram fórmulas. No sistema, viram **consultas calculadas em tempo real**
(contagens, taxa de aprovação, funil, dias parado, semáforo NO PRAZO/ATRASADO).
Isso elimina o risco de fórmula quebrada e mantém o número sempre coerente com os dados.

## 4. Lógica de negócio migrada
- **Dias parado**: `hoje − data da 2ª etapa` (propriedade do candidato).
- **Situação da fila**: `ATRASADO` se dias parado > SLA (padrão 3, ajustável por query).
- **Taxa de aprovação**: aprovados ÷ cadastrados.
- **Em processo**: status que não é final (APROVADO/REPROVADO/DECLINOU/DESISTIU/SEM RETORNO).
- **Vagas em aberto**: status ≠ FECHADA.

## 5. Decisões e trade-offs
- **SQLite por padrão** para rodar em 1 comando; troca para Postgres só mudando a variável `DATABASE_URL`.
- **`create_all` no boot** cria as tabelas automaticamente. Para produção com histórico de
  mudanças de schema, adotar **Alembic** (migrations).
- **CORS liberado (`*`)** para facilitar o desenvolvimento do front — restringir às origens reais em produção.
- **Sem autenticação ainda** (ver roadmap).

## 6. Roadmap sugerido (próximas fases)
1. **Autenticação e perfis** (RH, gestor, diretoria) — JWT ou OAuth interno.
2. **Migrations com Alembic** antes de ir para produção.
3. **E-mail automático ao gestor** quando um candidato entra na fila de parecer
   (a planilha já coleta o e-mail do gestor exatamente para isso).
4. **Front-end** — React (ou HTMX se quiser algo mais simples) consumindo estes endpoints.
5. **Auditoria** — registrar quem alterou parecer/status e quando.
6. **Deploy** — container Docker + Postgres gerenciado.

## 7. Como o front conversa com a API
Exemplos:
```
GET  /candidatos?status=APROVADO
PATCH /candidatos/42   { "status": "APROVADO", "etapa_atual": "6. Aprovado" }
GET  /fila-gestao?sla_dias=2
GET  /painel
```
Toda a especificação fica visível e testável em `/docs`.
