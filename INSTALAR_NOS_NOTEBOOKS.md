# Instalar o ATS nos notebooks da equipe

Há dois caminhos. **O primeiro é o recomendado** para uso em equipe.

---

## Caminho 1 — Atalho para o servidor  ✅ recomendado

Todos usam o **mesmo sistema e o mesmo banco**. Cada notebook recebe só um
ícone que abre o app em janela própria, sem barra de navegador.

### Como fazer em cada notebook

1. Copie para o notebook os arquivos **`criar_atalho.bat`** e **`ats.ico`**
2. Dê dois cliques em `criar_atalho.bat`
3. Informe o endereço do sistema, por exemplo:
   - `https://ats.tlmequipamentos.com.br` (nuvem)
   - `http://192.168.0.10:8000` (servidor na rede da empresa)
4. Pronto: o ícone **ATS - Recrutamento** aparece na Área de Trabalho

Não instala nada, não precisa de Python, e atualizações do sistema chegam
sozinhas — porque o programa está no servidor, não no notebook.

> **No servidor, rode o `baixar_bibliotecas.bat` uma vez.** Sem isso, o
> navegador de cada pessoa precisa buscar React e Tailwind na internet toda vez
> que abre o sistema — e a tela fica branca se a rede bloquear esses sites.

### No celular
- **Android (Chrome):** menu ⋮ → *Adicionar à tela inicial*
- **iPhone (Safari):** compartilhar → *Adicionar à Tela de Início*

---

## Caminho 2 — Programa instalado (.exe)

Gera um `ATS-TLM.exe` que roda sozinho, sem instalar Python.

```
gerar_exe.bat        (leva de 2 a 5 minutos; gera dist\ATS-TLM.exe)
```

### ⚠️ Cuidado importante

O `.exe` carrega **o próprio banco de dados**, na pasta onde ele está.
Se cinco pessoas rodarem cada uma o seu, você terá **cinco bancos
separados** — a Vanessa não veria o que o Samuel cadastrou, e os
relatórios ficariam errados.

Use o `.exe` apenas quando:

- for **um único computador** usando o sistema; ou
- o `.exe` estiver configurado para um **PostgreSQL central**
  (variável `DATABASE_URL`), caso em que o banco é compartilhado.

Para equipe, prefira o **Caminho 1**.

---

## Comparação rápida

| | Atalho (servidor) | Programa (.exe) |
|---|---|---|
| Dados compartilhados | sim | não (a menos que use banco central) |
| Instala algo no notebook | não | sim |
| Atualizar o sistema | uma vez, no servidor | em cada notebook |
| Funciona fora da empresa | sim (na nuvem) | só naquele computador |
| Acesso pelo celular | sim | não |
| Backup | um só, no servidor | um por notebook |

---

## Resumindo

- **Equipe (RH, gestores, diretoria)** → Caminho 1
- **Só você, num computador** → Caminho 2 serve
