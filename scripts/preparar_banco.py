"""
Prepara o banco antes do sistema subir.

Roda UMA vez (no arranque do container, antes dos processos do servidor),
para evitar que varios processos facam a mesma coisa ao mesmo tempo e
acabem duplicando as listas iniciais.

Uso:  python -m scripts.preparar_banco
"""
import sys

sys.path.insert(0, ".")

from app.esquema import preparar


def main():
    print("Preparando o banco...")
    preparar()
    print("Banco pronto.")


if __name__ == "__main__":
    main()
