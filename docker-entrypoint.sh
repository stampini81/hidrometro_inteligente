#!/bin/sh
set -e
CODE_DIR="/app/MVC_sistema_leitura_hidrometros"
APP_PATH="${CODE_DIR}/app"
cd "${CODE_DIR}" || echo "[ENTRYPOINT] Aviso: não foi possível entrar em ${CODE_DIR}"
export PYTHONPATH="${CODE_DIR}:$PYTHONPATH"
if [ "${AUTO_MIGRATE}" = "1" ]; then
  echo "[ENTRYPOINT] Inicializando banco (create_all + admin)."
  python3 - <<'PY'
import os, sys, pathlib
# Busca dinâmica pelo diretório que contém o pacote app
for path in [pathlib.Path.cwd()] + list(pathlib.Path('/app').rglob('*')):
  if (path / 'app' / '__init__.py').exists():
    if str(path) not in sys.path:
      sys.path.insert(0, str(path))
    break
try:
  from app import app, db  # type: ignore
  from sqlalchemy import inspect
  from app.models.usuario_model import Usuario  # type: ignore
except ModuleNotFoundError as e:
  print('[ENTRYPOINT] Falha import app:', e)
  raise SystemExit(1)
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

echo "[ENTRYPOINT] Iniciando aplicação Flask (run.py)"
exec python3 /app/MVC_sistema_leitura_hidrometros/run.py
