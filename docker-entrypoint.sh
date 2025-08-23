#!/bin/sh
set -e
BASE_PKG_DIR="MVC_sistema_leitura_hidrometros/MVC_sistema_leitura_hidrometros"
APP_PATH="${BASE_PKG_DIR}/app"
export PYTHONPATH="/app/${BASE_PKG_DIR}:$PYTHONPATH"
if [ "${AUTO_MIGRATE}" = "1" ]; then
  echo "[ENTRYPOINT] Inicializando banco (create_all + admin)."
  python - <<'PY'
import os
from app import app, db
from sqlalchemy import inspect
from app.models.usuario_model import Usuario
with app.app_context():
  db.create_all()
  insp = inspect(db.engine)
  print('[ENTRYPOINT] Tabelas criadas/detectadas:', insp.get_table_names())
  admin_pass = os.environ.get('ADMIN_PASSWORD','admin')
  if 'Usuario' in insp.get_table_names() and not Usuario.query.filter_by(username='admin').first():
    u = Usuario(username='admin', role='admin')
    u.set_password(admin_pass)
    db.session.add(u)
    try:
      db.session.commit(); print('[ENTRYPOINT] Usuário admin criado.')
    except Exception as e:
      db.session.rollback(); print('[ENTRYPOINT] Falha ao criar admin:', e)
PY
fi

exec python MVC_sistema_leitura_hidrometros/MVC_sistema_leitura_hidrometros/run.py
