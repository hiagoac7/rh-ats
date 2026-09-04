"""
Valores iniciais das listas do sistema (vindos da aba LISTAS da planilha).
Servem apenas para popular o banco na primeira execucao — depois de criados,
os valores sao editaveis pela tela de Configuracoes.
"""

LISTAS_PADRAO = {
    "criterio_avaliacao": [
        "Experiência na função",
        "Comunicação",
        "Perfil comportamental",
        "Disponibilidade",
        "Aderência à cultura",
    ],

    "cargo": ["Analista COMEX", "Analista de Marketing", "Analista de TI", "Assistente ADM Comercial",
              "Assistente de RH", "Auxiliar de Compras", "Auxiliar de Mecânico", "BDR",
              "Coordenador de Produto COMEX", "Executivo COMEX", "Gerente de Marketing", "Mecânico",
              "SDR", "Social Media", "Supervisor Comercial", "Supervisor SDR",
              "Técnico de Atendimento", "Vendedor", "Vendedor Externo"],
    "origem": ["Indeed", "LinkedIn", "E-mail", "Indicação", "WhatsApp", "RHI", "Jobbol", "OLX",
               "Presencial", "EmpregaPalhoça"],
    "area": ["Gestão Pessoas", "Operação", "Marketing", "Comercial", "Pós Vendas", "COMEX",
             "Administrativo", "Compras"],
    "nivel": ["Júnior", "Pleno", "Sênior", "Júnior/Pleno", "Pleno/Sênior", "Júnior/Pleno/Sênior"],
    "tipo_contrato": ["CLT", "PJ", "CLT/PJ", "Estágio", "Temporário"],
    "motivo": ["AMPLIAÇÃO", "SUBSTITUIÇÃO"],
    "status_vaga": ["ABERTURA", "DIVULGAÇÃO", "PERFIL", "SELEÇÃO", "CONGELADA", "FECHADA"],
    "status_candidato": ["TRIADO", "RH", "GESTÃO", "CONGELADA", "FECHADA",
                         "APROVADO", "REPROVADO", "DECLINOU", "DESISTIU", "SEM RETORNO", "CANCELADO"],
    "etapa": ["1. Recebido", "2. Triado", "3. Entrevista RH", "4. Entrevista Gestão",
              "5. Congelado", "6. Aprovado", "0. Encerrado"],
    "linha": ["Linha Amarela", "Linha Movimentação", "Ambas"],
    "reagendado": ["Não", "Sim, pelo RH", "Sim, pelo candidato"],
    "acesso_ti": ["E-mail corporativo", "Usuário de rede", "ERP", "Computador / notebook",
                  "Telefone / ramal", "Crachá", "Acesso ao sistema de RH", "Grupo de WhatsApp"],
}

ROTULOS = {
    "cargo": "Cargos", "origem": "Origens do candidato", "area": "Áreas da empresa",
    "nivel": "Níveis", "tipo_contrato": "Tipos de contrato", "motivo": "Motivos da vaga",
    "status_vaga": "Status da vaga", "status_candidato": "Status do candidato",
    "etapa": "Etapas do funil", "linha": "Linhas (Vendedor/SDR)", "reagendado": "Opções de reagendamento",
    "criterio_avaliacao": "Critérios da avaliação de entrevista",
}

SENSIVEIS = {"etapa", "status_candidato"}
