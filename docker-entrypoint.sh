#!/bin/sh
set -e
APP_PATH="MVC_sistema_leitura_hidrometros/MVC_sistema_leitura_hidrometros/app"
if [ "${AUTO_MIGRATE}" = "1" ]; then
  echo "[ENTRYPOINT] Executando migrações (se existirem)..."
  # Usamos diretório raiz /app/migrations (padrão Flask-Migrate); não depende de estar dentro do pacote.
  if [ ! -d "/app/migrations" ]; then
    echo "[ENTRYPOINT] Criando estrutura de migrações..."
    flask --app ${APP_PATH} db init || true
  fi
  flask --app ${APP_PATH} db migrate -m "auto" || true
  flask --app ${APP_PATH} db upgrade || echo "[ENTRYPOINT] upgrade falhou (pode ser inicial)" 

  # Verifica se tabela Cliente existe; se não, cria tudo via create_all (fallback)
  python - <<'PY'
from app import db, app
from sqlalchemy import inspect
with app.app_context():
    insp = inspect(db.engine)
    tables = insp.get_table_names()
    if 'Cliente' not in tables:
        print('[ENTRYPOINT] Tabela Cliente ausente após migrações. Executando create_all() fallback...')
        db.create_all()
        print('[ENTRYPOINT] Tabelas agora:', inspect(db.engine).get_table_names())
    else:
        print('[ENTRYPOINT] Tabelas detectadas:', tables)
PY
fi

exec python MVC_sistema_leitura_hidrometros/MVC_sistema_leitura_hidrometros/run.py
