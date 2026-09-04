"""
Versao "programa de computador" do ATS.

Sobe o sistema em segundo plano e abre a janela do aplicativo automaticamente.
Usado para gerar um .exe unico com o PyInstaller (veja gerar_exe.bat).

ATENCAO — leia antes de distribuir:
  Se cada pessoa rodar o .exe no proprio notebook, cada uma tera o SEU banco,
  e os dados NAO serao compartilhados. Use esta versao apenas se:
    (a) for um unico computador; ou
    (b) o DATABASE_URL apontar para um PostgreSQL central.
  Para varias pessoas, prefira o servidor + atalho (criar_atalho.bat).
"""
import os
import socket
import sys
import threading
import time
import webbrowser

BASE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE)
os.chdir(os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else BASE)


def porta_livre(inicio: int = 8000, fim: int = 8020) -> int:
    for p in range(inicio, fim):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    return inicio


def abrir_janela(url: str):
    """Abre em janela propria (sem barra de navegador), se houver Edge/Chrome."""
    time.sleep(2.0)
    candidatos = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
    ]
    for nav in candidatos:
        if os.path.exists(nav):
            os.spawnl(os.P_NOWAIT, nav, f'"{nav}"', f"--app={url}")
            return
    webbrowser.open(url)


def main():
    import uvicorn
    porta = porta_livre()
    url = f"http://127.0.0.1:{porta}"
    print("=" * 46)
    print("  ATS TLM — Recrutamento e Selecao")
    print("=" * 46)
    print(f"  Abrindo em {url}")
    print("  Para encerrar, feche esta janela.")
    print("=" * 46)
    threading.Thread(target=abrir_janela, args=(url,), daemon=True).start()
    uvicorn.run("app.main:app", host="127.0.0.1", port=porta, log_level="warning")


if __name__ == "__main__":
    main()
