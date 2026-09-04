# Acesso de fora da empresa (home office e celular)

Dois caminhos. O **A** funciona hoje e é gratuito; o **B** é o definitivo.

---

## A) Túnel Cloudflare — funciona hoje, sem custo

O sistema continua rodando no computador da empresa, mas ganha um endereço
público com HTTPS. A Vanessa acessa de casa normalmente.

**Como funciona:** um programinha cria um "túnel" seguro entre o computador
da empresa e a Cloudflare. Não precisa abrir portas no roteador, não precisa
IP fixo, e o certificado HTTPS é automático.

### Passo a passo

1. **Criar conta grátis** em `dash.cloudflare.com` e adicionar o domínio
   da empresa (`tlmequipamentos.com.br`).
   > Isso exige apontar os servidores DNS do domínio para a Cloudflare —
   > o provedor atual do site continua funcionando normalmente.

2. **Instalar o programa** no computador que roda o sistema:
   - Baixe `cloudflared` para Windows em
     `https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/`
   - Instale (é um `.msi`, next-next-finish)

3. **Criar o túnel** — abra o Prompt de Comando e rode:
   ```
   cloudflared tunnel login
   cloudflared tunnel create ats
   cloudflared tunnel route dns ats ats.tlmequipamentos.com.br
   ```

4. **Ligar o túnel** apontando para o sistema:
   ```
   cloudflared tunnel run --url http://localhost:8000 ats
   ```

5. **Deixar rodando sozinho** (para não depender de janela aberta):
   ```
   cloudflared service install
   ```

Pronto: `https://ats.tlmequipamentos.com.br` funciona de qualquer lugar.

### O que considerar
- O computador da empresa precisa ficar **ligado** (é ele que roda o sistema)
- Se a internet da empresa cair, o acesso cai junto
- Custo: **zero** (o plano gratuito da Cloudflare cobre isso com folga)
- Bom para: começar rápido, testar com a equipe, ganhar tempo

---

## B) Servidor na nuvem — o definitivo

O sistema sai do computador da empresa e passa a viver num servidor que
fica ligado 24 horas, com backup automático.

- Passo a passo completo: **`PUBLICAR.md`**
- Custo: R$ 35 a 60 por mês
- Não depende de ninguém deixar computador ligado
- Não depende da internet da empresa
- Bom para: uso definitivo, com o RH inteiro dependendo do sistema

---

## Recomendação prática

1. **Esta semana:** ligue o túnel (A). A Vanessa já trabalha de casa,
   e você testa o sistema com gente de verdade sem gastar nada.
2. **Nas próximas semanas:** contrate o servidor (B) e migre.
   Como o endereço é o mesmo (`ats.tlmequipamentos.com.br`), basta
   apontá-lo para o servidor novo — ninguém precisa mudar nada no notebook.

---

## Segurança — vale para os dois caminhos

Ao expor o sistema para a internet, ele passa a guardar CPF, telefone e
e-mail de candidatos num endereço público. Confira antes de liberar:

- [ ] Cada pessoa com **seu** login e senha própria (nunca compartilhar)
- [ ] Senhas fortes — o sistema exige no mínimo 6 caracteres, mas peça mais
- [ ] Perfis corretos: TI administra, RH opera, gestor dá parecer, diretoria só vê
- [ ] Backup rodando e testado
- [ ] HTTPS ativo (cadeado no navegador) — os dois caminhos já garantem isso

> Se um dia alguém sair da empresa, **desative o usuário** na aba Gestão.
> O histórico do que a pessoa fez continua na Auditoria.
