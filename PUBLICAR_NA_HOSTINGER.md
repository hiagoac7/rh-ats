# Publicar o ATS usando seu domínio .br e a Hostinger

Guia para a situação real da TLM: domínio `.com.br` já registrado, site
institucional no Wix, e hospedagem na Hostinger.

---

## Antes de tudo: o que serve e o que não serve

| Onde | Serve para o ATS? | Por quê |
|---|---|---|
| **Wix** | **Não** | É um construtor de sites fechado. Você publica páginas, não roda programas. Não há como instalar Python, Docker ou banco de dados. |
| **Hostinger — hospedagem compartilhada** | **Não** | Roda scripts PHP/Python simples, mas não um servidor que fica ligado o tempo todo. O ATS mantém uma conexão aberta com cada navegador (é isso que atualiza as telas sozinhas) e a hospedagem compartilhada corta esse tipo de conexão. |
| **Hostinger — VPS** | **Sim** | É um servidor Linux seu, com acesso total. Roda Docker, PostgreSQL e o ATS exatamente como no `docker-compose.yml` deste projeto. |

**Resumo:** contrate um **VPS na Hostinger**. O site do Wix continua onde está,
intocado. O ATS ganha um endereço próprio, tipo
`ats.tlmequipamentos.com.br`, apontando para o VPS.

---

## Passo 1 — Contratar o VPS (10 min)

No painel da Hostinger, procure **VPS** (não "Hospedagem de Sites").

- **Plano:** o mais barato costuma bastar. O ATS + PostgreSQL rodam
  confortavelmente em **2 GB de RAM**. Com 15 pessoas usando ao mesmo tempo,
  4 GB dá folga tranquila.
- **Sistema operacional:** na tela *"Escolha o que instalar"* há três abas.

  | Aba | O que fazer |
  |---|---|
  | **Aplicativos** | **Comece por aqui.** Procure **Docker** (costuma aparecer como "Ubuntu com Docker"). Escolhendo esta, o Passo 3 fica desnecessário. |
  | **Apenas SO** | Se não houver Docker na aba anterior, escolha **Ubuntu** (versão mais recente). Instale o Docker no Passo 3. |
  | **Painel de controle** | **Não use.** Veja o aviso abaixo. |

  > **Evite cPanel, CyberPanel, Plesk e afins.** Esses painéis instalam um
  > servidor web próprio que ocupa as **portas 80 e 443** — exatamente as que
  > o sistema usa para o HTTPS automático. Daria conflito, e desfazer depois
  > dá mais trabalho do que instalar do zero. O ATS não precisa de painel:
  > ele já traz o seu próprio servidor web dentro do Docker.
- **Localização:** prefira **Brasil** ou **São Paulo**, se houver. Quanto mais
  perto, mais rápido para o RH.

Ao terminar, a Hostinger mostra o **IP do servidor** (algo como `191.x.x.x`) e
a **senha de root**. Guarde os dois.

---

## Passo 2 — Apontar o subdomínio (5 min + espera)

Aqui é onde o Wix e a Hostinger convivem: você **não mexe** no site principal,
só cria um endereço novo ao lado.

Vá onde o **DNS do domínio** é gerenciado. Pode ser o Registro.br, a Hostinger
ou o próprio Wix — depende de onde você apontou os servidores de nome.
Se não souber, comece pelo Registro.br: ele mostra para quem o domínio aponta.

Crie um registro assim:

| Campo | Valor |
|---|---|
| Tipo | **A** |
| Nome / Host | **ats** |
| Aponta para / Valor | **o IP do VPS** |
| TTL | 3600 (ou o padrão) |

Isso cria `ats.tlmequipamentos.com.br`. O `www` e a raiz continuam no Wix.

> A propagação leva de minutos a algumas horas. Confira digitando
> `ats.tlmequipamentos.com.br` no navegador: enquanto não responder nada,
> ainda está propagando. **Não siga para o Passo 5 antes de responder**, senão
> o certificado HTTPS falha.

---

## Passo 3 — Instalar o Docker no VPS (5 min)

Conecte no servidor. No Windows, use o **PowerShell**:

```bash
ssh root@SEU_IP_AQUI
```

Depois, no servidor:

```bash
apt update && apt upgrade -y
curl -fsSL https://get.docker.com | sh
docker --version          # confirma que instalou
```

---

## Passo 4 — Enviar os arquivos (10 min)

No **seu computador**, dentro da pasta `rh_ats`, no PowerShell:

```powershell
scp -r app migrations scripts Dockerfile docker-compose.yml requirements.txt alembic.ini root@SEU_IP_AQUI:/opt/ats/
```

Se der erro dizendo que a pasta não existe, crie antes no servidor:

```bash
mkdir -p /opt/ats
```

> **Não envie** o arquivo `rh_ats.db` nem o `.chave_secreta`. O banco novo é
> PostgreSQL, e a chave é gerada no servidor. Levar os dados é o Passo 6.

---

## Passo 5 — Configurar e subir (10 min)

No servidor, crie o arquivo de configuração:

```bash
cd /opt/ats
nano .env
```

Cole isto, **trocando os valores**:

```
POSTGRES_PASSWORD=uma-senha-longa-e-aleatoria-aqui
SECRET_KEY=outra-coisa-longa-e-completamente-diferente
DOMINIO=ats.tlmequipamentos.com.br
EMAIL_ADMIN=ti@tlmequipamentos.com.br
```

Para gerar valores bons, rode no próprio servidor e copie o resultado:

```bash
openssl rand -base64 48
```

Salve com `Ctrl+O`, `Enter`, `Ctrl+X`.

> **A `SECRET_KEY` assina os logins.** Se você trocá-la depois, todo mundo é
> desconectado. Guarde no gerenciador de senhas da empresa.
> O arquivo `.env` **nunca** vai para o Git nem sai da empresa.

Agora suba:

```bash
docker compose up -d --build
```

A primeira vez demora alguns minutos (baixa imagens e compila). Acompanhe:

```bash
docker compose logs -f sistema
```

Quando aparecer `Uvicorn running`, abra `https://ats.tlmequipamentos.com.br`
no navegador. O **HTTPS é automático** — o Traefik pede o certificado gratuito
sozinho e renova sem você fazer nada.

---

## Passo 6 — Levar os dados que já existem (5 min)

O banco na nuvem começa vazio. Para levar os 312 candidatos:

**No seu computador**, envie o banco atual:

```powershell
scp rh_ats.db root@SEU_IP_AQUI:/opt/ats/
```

**No servidor**, coloque o arquivo dentro do container e rode a migração:

```bash
cd /opt/ats
docker compose cp rh_ats.db sistema:/app/rh_ats.db
docker compose exec sistema python -m scripts.migrar_para_postgres
```

> O primeiro comando é necessário: o programa roda **dentro** do container, e
> o container não enxerga as pastas do servidor. Sem essa cópia, a migração
> reclamaria que não achou o banco.

Confira o resultado — ele diz quantos candidatos e vagas foram levados.
Se estiver certo, **apague as duas cópias**, porque são dados do RH:

```bash
docker compose exec sistema rm -f /app/rh_ats.db
rm /opt/ats/rh_ats.db
```

Confirme pelo navegador que os candidatos apareceram antes de apagar.

---

## Passo 7 — Criar os acessos (5 min)

```bash
docker compose exec sistema python -m scripts.criar_admin
```

Crie o seu usuário TI. Depois, entre no sistema pelo navegador e cadastre a
Vanessa e o resto do RH em **Gestão**.

---

## Depois de no ar

**Backup — configure isto no primeiro dia.** No servidor:

```bash
crontab -e
```

Adicione a linha (backup todo dia às 2h da manhã):

```
0 2 * * * cd /opt/ats && docker compose exec -T banco pg_dump -U ats rh_ats | gzip > /opt/ats/backups/ats_$(date +\%Y\%m\%d).sql.gz
```

Crie a pasta antes: `mkdir -p /opt/ats/backups`

> Backup no mesmo servidor protege contra erro humano, **não** contra o
> servidor morrer. Uma vez por mês, baixe uma cópia para um computador da
> empresa: `scp root@SEU_IP:/opt/ats/backups/*.gz .`

**Atualizar o sistema** quando houver mudanças:

```bash
cd /opt/ats
docker compose up -d --build
```

**Desligar** (sem perder dados):

```bash
docker compose down
```

> **NUNCA** use `docker compose down -v`. O `-v` apaga os volumes e, com eles,
> **todo o banco do RH**.

---

## O que muda para o RH

- Acessam por `https://ats.tlmequipamentos.com.br`, de qualquer lugar
- A **Vanessa em home office** entra igual, sem VPN
- Ninguém precisa mais do `iniciar.bat` — o servidor fica ligado sozinho
- Funciona no celular pelo navegador

Para deixar com cara de aplicativo, use o `criar_atalho.bat` apontando para o
endereço novo (veja `INSTALAR_NOS_NOTEBOOKS.md`).

---

## Custo aproximado

| Item | Ordem de grandeza |
|---|---|
| VPS Hostinger (2–4 GB) | faixa de R$ 30 a R$ 60 por mês |
| Domínio `.com.br` | você já tem |
| Certificado HTTPS | gratuito (Let's Encrypt, automático) |
| Wix | continua como está, sem alteração |

Confira o valor atual no painel da Hostinger — preços mudam e costumam ter
desconto grande no primeiro período e renovação mais cara.

---

## Se algo der errado

| Sintoma | O que olhar |
|---|---|
| O endereço não abre | DNS ainda propagando, ou o registro **A** aponta para o IP errado |
| Abre mas dá erro de certificado | Subiu antes do DNS propagar. Rode `docker compose restart proxy` |
| Página em branco | `docker compose logs sistema` mostra o erro |
| "Sem conexão com o servidor" | `docker compose ps` — algum serviço caiu |
| Esqueceu a senha de alguém | Entre como TI e use **Gestão → senha** |
