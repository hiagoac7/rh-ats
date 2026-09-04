# Colocar o ATS na nuvem — passo a passo

Resultado: `https://ats.tlmequipamentos.com.br` acessível de qualquer lugar,
com HTTPS, banco PostgreSQL e backup diário automático.

**Tempo:** cerca de 1 hora · **Custo:** R$ 35 a 60 por mês

---

## Antes de começar, tenha em mãos

- Cartão para contratar o servidor
- Acesso ao painel de DNS do domínio `tlmequipamentos.com.br`
- O arquivo `rh_ats.db` (os dados atuais)

---

## Passo 1 — Contratar o servidor (10 min)

Recomendo a **Hostinger VPS** (interface em português, suporte em português,
pagamento em reais). Plano **KVM 2**: 2 vCPU, 8 GB RAM — sobra para 15 pessoas.

1. Acesse `hostinger.com.br` → VPS → escolha o **KVM 2**
2. Sistema operacional: **Ubuntu 24.04**
3. Defina uma senha de root e **guarde**
4. Ao final, anote o **endereço IP** do servidor

> Alternativas equivalentes: Contabo (mais barato, suporte em inglês),
> DigitalOcean, Magalu Cloud.

## Passo 2 — Apontar o endereço (5 min + espera)

No painel de DNS do domínio da empresa, crie:

```
Tipo: A     Nome: ats     Valor: <IP do servidor>     TTL: automático
```

Isso cria `ats.tlmequipamentos.com.br`. A propagação leva de 5 minutos a 2 horas.

Para conferir, no seu computador: `nslookup ats.tlmequipamentos.com.br`

## Passo 3 — Enviar os arquivos (10 min)

No painel da Hostinger existe um **terminal pelo navegador** — dá para usar
ele e pular o SSH.

Envie para o servidor, na pasta `/opt/ats`, estes itens da pasta do sistema:

```
app/          migrations/     scripts/
Dockerfile    docker-compose.yml
requirements.txt   alembic.ini
.env.exemplo  backup_postgres.sh   deploy.sh
rh_ats.db     (os dados atuais)
```

Jeito mais simples: compacte tudo num `.zip`, envie por
[WinSCP](https://winscp.net) ou pelo gerenciador de arquivos do painel,
e descompacte com `unzip arquivo.zip -d /opt/ats`.

## Passo 4 — Subir o sistema (10 min)

No terminal do servidor:

```bash
cd /opt/ats
bash deploy.sh
```

Na primeira vez ele cria o arquivo `.env` com senha e chave **geradas
automaticamente** e pede para você preencher o domínio:

```bash
nano .env
```

Preencha:
```
DOMINIO=ats.tlmequipamentos.com.br
EMAIL_ADMIN=ti@tlmequipamentos.com.br
```
(salve com `Ctrl+O`, `Enter`, e saia com `Ctrl+X`)

Rode de novo:
```bash
bash deploy.sh
```

Ele instala tudo, sobe o sistema, configura o HTTPS e agenda o backup diário.

## Passo 5 — Levar os dados (5 min)

```bash
docker compose exec sistema python -m scripts.migrar_para_postgres
```

Ele copia candidatos, vagas, usuários, anotações e acessos.
O `rh_ats.db` **não é alterado** — continua como cópia de segurança.

> Se preferir começar do zero:
> ```bash
> docker compose exec sistema python -m scripts.criar_admin \
>   "Hiago TI" ti@tlmequipamentos.com.br SuaSenhaForte TI
> ```

## Passo 6 — Testar (5 min)

Abra `https://ats.tlmequipamentos.com.br`

- [ ] Aparece o cadeado de segurança no navegador
- [ ] Consegue entrar com seu login
- [ ] Os candidatos e vagas estão lá
- [ ] Abre no celular

## Passo 7 — Liberar para a equipe (5 min por pessoa)

1. No sistema: aba **Gestão** → *Novo usuário* (papel certo para cada um)
2. No notebook da pessoa: copie `criar_atalho.bat` e `ats.ico`, rode e
   informe `https://ats.tlmequipamentos.com.br`
3. No celular: abrir o endereço → *Adicionar à tela inicial*

---

## Depois: o que manter de olho

| Quando | O quê |
|---|---|
| Toda semana | Confirmar que o backup está sendo gerado (`ls /opt/ats/backups`) |
| Todo mês | Baixar uma cópia do backup para fora do servidor |
| A cada 3 meses | Testar restaurar um backup (backup não testado não é backup) |
| Quando alguém sair | Desativar o usuário na aba Gestão |

### Comandos úteis

```bash
cd /opt/ats
docker compose logs -f sistema     # ver o que está acontecendo
docker compose restart sistema     # reiniciar
docker compose ps                  # ver se está tudo no ar
docker compose down                # desligar
```

### Atualizar o sistema depois
```bash
cd /opt/ats
# substitua os arquivos alterados (app/, migrations/, etc.)
docker compose up -d --build
```
As migrations rodam sozinhas e **os dados são preservados**.
