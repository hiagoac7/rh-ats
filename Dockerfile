# Imagem do sistema ATS — usada na publicacao em nuvem
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=America/Sao_Paulo

WORKDIR /app

# dependencias primeiro (aproveita o cache quando so o codigo muda)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY app ./app
COPY migrations ./migrations
COPY scripts ./scripts
COPY alembic.ini .

# Traz React, Babel, Tailwind e Chart.js para dentro da imagem.
# Sem isto, o navegador de cada usuario buscaria essas bibliotecas em
# unpkg.com/cdn.tailwindcss.com a cada abertura — e o sistema ficaria fora
# do ar sempre que a rede do usuario bloqueasse esses sites.
# "|| true": se a build rodar sem internet, a imagem ainda sobe e o front
# cai para os CDNs sozinho.
RUN python -m scripts.baixar_bibliotecas || true

# usuario sem privilegios (boa pratica de seguranca)
RUN useradd -m -u 1000 ats && chown -R ats:ats /app
USER ats

EXPOSE 8000

# aplica as migrations e sobe o servidor
# 1) atualiza o esquema  2) prepara o banco uma unica vez  3) sobe o servidor
# timeout 0: as conexoes de tempo real ficam abertas de proposito e nao podem
#            ser derrubadas por inatividade (os workers sao assincronos)
CMD alembic upgrade head && \
    python -m scripts.preparar_banco && \
    gunicorn app.main:app \
      --worker-class uvicorn.workers.UvicornWorker \
      --workers 3 --bind 0.0.0.0:8000 \
      --timeout 0 --graceful-timeout 30 --keep-alive 75 \
      --access-logfile -
