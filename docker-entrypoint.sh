#!/bin/sh
set -e
APP_PATH="MVC_sistema_leitura_hidrometros/MVC_sistema_leitura_hidrometros/app"
if [ "${AUTO_MIGRATE}" = "1" ]; then
  echo "[ENTRYPOINT] Executando migrações (se existirem)..."
  # Inicializa repositório de migrações se ainda não existe diretório migrations dentro do app
  if [ ! -d "${APP_PATH}/migrations" ]; then
    echo "[ENTRYPOINT] Criando estrutura de migrações..."
    flask --app ${APP_PATH} db init || true
  fi
  flask --app ${APP_PATH} db migrate -m "auto" || true
  flask --app ${APP_PATH} db upgrade || {
    echo "[ENTRYPOINT] Falha ao aplicar migrações. Tentando criar tabelas direto...";
    python - <<'PY'
from app import db, app
with app.app_context():
    db.create_all()
    print('[ENTRYPOINT] create_all executado.')
PY
  }
fi

exec python MVC_sistema_leitura_hidrometros/MVC_sistema_leitura_hidrometros/run.py
