#!/bin/sh
set -e
APP_PATH="MVC_sistema_leitura_hidrometros/MVC_sistema_leitura_hidrometros/app"
if [ "${AUTO_MIGRATE}" = "1" ]; then
  echo "[ENTRYPOINT] Migrações automáticas via API Flask-Migrate"
  python - <<'PY'
import os
from app import app, db
from sqlalchemy import inspect
from flask_migrate import upgrade, migrate, init, stamp
from pathlib import Path
from app.models.usuario_model import Usuario

with app.app_context():
  mig_dir = Path('migrations')
  if not mig_dir.exists():
    print('[ENTRYPOINT] migrations/ ausente -> init')
    init()
    # Marca head vazio para evitar erro em upgrade inicial
    stamp()
  try:
    migrate(message='auto')
  except Exception as e:
    print('[ENTRYPOINT] migrate falhou (pode ser sem mudanças):', e)
  try:
    upgrade()
  except Exception as e:
    print('[ENTRYPOINT] upgrade falhou, tentando create_all fallback:', e)
    db.create_all()
  insp = inspect(db.engine)
  print('[ENTRYPOINT] Tabelas:', insp.get_table_names())
  # Garante admin
  admin_pass = os.environ.get('ADMIN_PASSWORD','admin')
  if 'Usuario' in insp.get_table_names() and not Usuario.query.filter_by(username='admin').first():
    u = Usuario(username='admin', role='admin')
    u.set_password(admin_pass)
    db.session.add(u)
    try:
      db.session.commit()
      print('[ENTRYPOINT] Usuário admin criado')
    except Exception as e:
      db.session.rollback()
      print('[ENTRYPOINT] Falha ao criar admin:', e)
PY
fi

exec python MVC_sistema_leitura_hidrometros/MVC_sistema_leitura_hidrometros/run.py
