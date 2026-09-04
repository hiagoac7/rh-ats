# Publicar o sistema para o RH e os gestores

Objetivo: acesso de qualquer lugar (escritório, casa, celular), com HTTPS,
banco PostgreSQL e backup automático. Tempo estimado: 1 a 2 horas.

---

## Resumo do caminho

1. Contratar um servidor pequeno na nuvem
2. Apontar um endereço (ex.: `ats.tlmequipamentos.com.br`) para ele
3. Subir o sistema com um comando
4. Levar os dados que já existem
5. Ligar o backup automático

---

## 1. Servidor

Qualquer provedor serve. Opções comuns no Brasil:

| Provedor | Plano | Preço aproximado |
|---|---|---|
| Hostinger VPS | 2 vCPU / 8 GB | R$ 35–60 /mês |
| DigitalOcean | 2 vCPU / 2 GB | US$ 18 /mês |
| Contabo | 4 vCPU / 8 GB | € 6 /mês |
| Magalu Cloud / Locaweb | equivalente | R$ 50–90 /mês |

Para 5 a 15 pessoas, **2 vCPU e 4 GB de memória sobram**.
Escolha **Ubuntu 24.04** ao criar.

> Se a empresa já tem um servidor próprio ou VM no escritório com acesso
> externo, ele serve — pule para o passo 3.

## 2. Endereço (domínio)

No painel de DNS do domínio da empresa, crie um registro:

```
Tipo: A     Nome: ats     Valor: <IP do servidor>
```

Isso cria `ats.tlmequipamentos.com.br`. O certificado HTTPS é emitido
sozinho pelo sistema, gratuito, e se renova automaticamente.

## 3. Subir o sistema

Conecte no servidor (pelo terminal do provedor ou por SSH) e rode:

```bash
# instala o Docker
curl -fsSL https://get.docker.com | sh

# cria a pasta e envia os arquivos do sistema para ela
mkdir -p /opt/ats && cd /opt/ats
# (copie para cá: app/, migrations/, scripts/, Dockerfile,
#  docker-compose.yml, requirements.txt, alembic.ini, backup_postgres.sh)

# configuração
cp .env.exemplo .env
nano .env        # preencha senha, chave, domínio e e-mail

# gerar uma chave forte para o .env:
openssl rand -base64 48

# subir
docker compose up -d --build
```

Pronto: `https://ats.tlmequipamentos.com.br` já responde.

Comandos úteis:

```bash
docker compose logs -f sistema   # ver o que está acontecendo
docker compose restart sistema   # reiniciar
docker compose down              # desligar
```

## 4. Levar os dados atuais

No seu computador, gere um backup do banco atual e envie o arquivo
`rh_ats.db` para o servidor (pasta `/opt/ats`). Depois, no servidor:

```bash
docker compose exec sistema python -m scripts.migrar_para_postgres
```

Ele copia tudo — candidatos, vagas, usuários, anotações, acessos —
e **não altera** o arquivo original, que fica como cópia de segurança.

Se preferir começar do zero, basta criar o primeiro usuário:

```bash
docker compose exec sistema python -m scripts.criar_admin \
  "Hiago TI" ti@tlmequipamentos.com.br SuaSenhaForte TI
```

## 5. Backup automático

```bash
chmod +x backup_postgres.sh
crontab -e
# acrescente a linha (backup todo dia às 2h):
0 2 * * * /opt/ats/backup_postgres.sh
```

Guarda os últimos 30 dias em `/opt/ats/backups`.
**Leve uma cópia para fora do servidor** (Google Drive, OneDrive, outro HD).

---

## Segurança — o que conferir antes de liberar

- [ ] `.env` com senha e chave próprias (nunca as do exemplo)
- [ ] O arquivo `.env` **não** vai para o Git nem sai da empresa
- [ ] HTTPS funcionando (cadeado no navegador)
- [ ] Cada pessoa com o **seu** login — ninguém compartilha senha
- [ ] Perfis certos: TI administra, RH opera, gestor dá parecer, diretoria só vê
- [ ] Backup testado (restaure uma vez para ter certeza de que funciona)
- [ ] Senhas das plataformas de vagas num gerenciador, não em planilha

### Sobre dados pessoais (LGPD)
O sistema guarda nome, CPF, telefone, e-mail e histórico de candidatos.
Isso é dado pessoal. Recomendações práticas:

- Acesso só para quem precisa (as permissões já ajudam nisso)
- A auditoria registra quem viu e alterou o quê
- Combine um prazo para descartar candidatos antigos que não serão reaproveitados
- Informe no anúncio da vaga que os dados ficam guardados no processo seletivo

---

## No celular

O sistema funciona no navegador do celular. Para virar um ícone na tela:

- **Android (Chrome):** menu ⋮ → *Adicionar à tela inicial*
- **iPhone (Safari):** compartilhar → *Adicionar à Tela de Início*

Abre em tela cheia, com cara de aplicativo — sem precisar publicar em loja.

---

## Atualizar o sistema depois

```bash
cd /opt/ats
# substitua os arquivos alterados
docker compose up -d --build
```

As migrations rodam sozinhas e **os dados são preservados**.
Rode `python scripts/verificar.py` antes de publicar qualquer mudança.
