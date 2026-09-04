"""
Versao do sistema.

Serve para um problema concreto e recorrente: o index.html e lido do disco a
cada abertura de pagina, mas o codigo Python fica na memoria do processo. Depois
de uma atualizacao, se ninguem reiniciar o servidor, o navegador carrega a tela
NOVA falando com uma API VELHA — e o sintoma e um "Not Found" sem explicacao.

A tela compara este numero com o dela. Se forem diferentes, avisa que basta
reiniciar, em vez de deixar a pessoa achando que o sistema quebrou.

Suba este numero sempre que mexer em rota, schema ou modelo.
"""
VERSAO = "2026.08.03.5"
