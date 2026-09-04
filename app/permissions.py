"""
Catálogo de permissões, grupos e mapa papel -> permissões (RBAC).

Padrão ATS/HRIS (menor privilégio + matriz recurso×ação):
  - ACESSO TOTAL é exclusivo do TI (inclui gerenciar usuários, papéis e permissões);
  - RH tem tudo do recrutamento, MENOS a administração de acessos (isso é do TI);
  - GESTOR e DIRETORIA seguem o menor privilégio;
  - cada usuário pode ter ajustes finos (extras concedidas / negadas).
Permissão efetiva = (permissões do papel ∪ extras) − negadas.
"""

PERMISSOES = {
    "painel.ver":         "Ver painel e indicadores",
    "relatorios.exportar":"Exportar dados (CSV)",
    "vagas.ver":          "Ver vagas",
    "vagas.criar":        "Criar vagas",
    "vagas.editar":       "Editar / fechar vagas",
    "vagas.reabrir":      "Reabrir vaga (nova abertura do cargo)",
    "vagas.excluir":      "Excluir vaga",
    "candidatos.ver":     "Ver candidatos",
    "candidatos.criar":   "Cadastrar candidatos",
    "candidatos.editar":  "Editar dados do candidato",
    "candidatos.parecer": "Dar parecer / mudar status e etapa",
    "candidatos.anotar":  "Escrever anotações no candidato",
    "candidatos.excluir": "Excluir candidato",
    "fila.ver":           "Ver fila de parecer da gestão",
    "gestores.gerenciar": "Cadastrar / editar gestores",
    "canais.gerenciar":   "Gerenciar canais de divulgação",
    "listas.gerenciar":   "Configurar listas (cargos, origens, etapas...)",
    "email.configurar":   "Configurar o envio de e-mails",
    "email.enviar":       "Enviar e-mail / mensagem ao candidato",
    "requisicoes.criar":  "Solicitar abertura de vaga",
    "requisicoes.aprovar":"Aprovar ou recusar requisições de vaga",
    "acessos.ver":        "Ver pedidos de acesso de novos contratados",
    "acessos.gerenciar":  "Dar baixa nos acessos criados",
    "auditoria.ver":      "Ver registro de auditoria",
    "usuarios.gerenciar": "Gerenciar usuários, papéis e permissões",
}
TODAS = set(PERMISSOES)

GRUPOS = {
    "Painel e relatórios":  ["painel.ver", "relatorios.exportar"],
    "Vagas":                ["vagas.ver", "vagas.criar", "vagas.editar", "vagas.reabrir", "vagas.excluir"],
    "Candidatos":           ["candidatos.ver", "candidatos.criar", "candidatos.editar", "candidatos.parecer", "candidatos.anotar", "candidatos.excluir"],
    "Processo seletivo":    ["fila.ver"],
    "Comunicação":          ["email.enviar", "email.configurar"],
    "Requisições":          ["requisicoes.criar", "requisicoes.aprovar"],
    "Acessos (TI)":         ["acessos.ver", "acessos.gerenciar"],
    "Gestão de RH":         ["gestores.gerenciar", "canais.gerenciar", "listas.gerenciar", "auditoria.ver"],
    "Administração (só TI)":["usuarios.gerenciar"],
}

ADMIN_TI = {"usuarios.gerenciar", "email.configurar"}

EXCLUSOES = {"vagas.excluir", "candidatos.excluir"}

ROLE_PERMS = {
    "TI": set(TODAS),
    "RH": set(TODAS) - ADMIN_TI - EXCLUSOES - {"acessos.gerenciar"},
    "GESTOR": {
        "painel.ver", "vagas.ver", "candidatos.ver",
        "candidatos.parecer", "candidatos.anotar", "fila.ver", "relatorios.exportar",
        "requisicoes.criar",
    },
    "DIRETORIA": {
        "painel.ver", "vagas.ver", "candidatos.ver",
        "relatorios.exportar",
        "requisicoes.aprovar",
    },
}


def perms_do_papel(perfil: str) -> set[str]:
    return set(ROLE_PERMS.get(perfil, set()))


def perms_efetivas(perfil: str, extras, negadas) -> set[str]:
    base = perms_do_papel(perfil)
    return (base | set(extras or [])) - set(negadas or [])
