"""
Regras de senha.

A recuperacao por e-mail foi retirada do sistema: o envio de e-mail nao e
confiavel neste ambiente e a pessoa ficava esperando um link que nunca chegava.
Quem perde o acesso fala com o TI, que troca a senha direto na tela de Gestao.

O que sobrou aqui e a unica coisa que continua valendo em qualquer caminho de
troca de senha: dizer se a senha escolhida serve.
"""
from __future__ import annotations

TAMANHO_MINIMO_SENHA = 8

FACEIS = {"12345678", "senha123", "password", "tlm12345", "abcd1234",
          "tlmequipamentos", "recrutamento"}


def problema_na_senha(senha: str) -> str | None:
    """Devolve a reclamacao, ou None se a senha serve."""
    if not senha or len(senha) < TAMANHO_MINIMO_SENHA:
        return f"A senha precisa ter pelo menos {TAMANHO_MINIMO_SENHA} caracteres."
    if senha.isdigit():
        return "Use letras também, não apenas números."
    if senha.lower() in FACEIS:
        return "Essa senha é fácil demais de adivinhar. Escolha outra."
    return None
