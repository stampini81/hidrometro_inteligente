import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega .env se existir (raiz do projeto ou pasta atual)
for p in [Path(__file__).parent.parent, Path(__file__).parent]:
    env_file = p / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        break

class Config:
    DEBUG = os.environ.get('DEBUG', '1') == '1'
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_key_change_me')

    # Preferência por MySQL se todas variáveis presentes
    DB_ENGINE = os.environ.get('DB_ENGINE', 'auto')  # auto, mysql, sqlite
    MYSQL_HOST = os.environ.get('DB_HOST', 'localhost')
    MYSQL_PORT = os.environ.get('DB_PORT', '3306')
    MYSQL_USER = os.environ.get('DB_USER', 'root')
    MYSQL_PASS = os.environ.get('DB_PASS', 'alunos')
    MYSQL_DB   = os.environ.get('DB_NAME', 'sistema_leitura_hidrometros')

    # Caminho SQLite (fallback)
    SQLITE_PATH = os.environ.get('SQLITE_PATH', str(Path(__file__).parent / 'instance' / 'app.db'))

    # Monta URI
    SQLALCHEMY_DATABASE_URI = ''
    if DB_ENGINE == 'mysql' or (DB_ENGINE == 'auto' and os.environ.get('DB_HOST')):
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASS}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    else:
        # Garante pasta
        sqlite_dir = Path(SQLITE_PATH).parent
        sqlite_dir.mkdir(parents=True, exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{SQLITE_PATH}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configurações MQTT
    MQTT_URL = os.environ.get('MQTT_URL', 'mqtt://broker.hivemq.com:1883')
    MQTT_TOPIC_DADOS = os.environ.get('MQTT_TOPIC_DADOS', 'hidrometro/leandro/dados')
    MQTT_TOPIC_CMD = os.environ.get('MQTT_TOPIC_CMD', 'hidrometro/leandro/cmd')

    # Limite de histórico em memória
    HISTORY_LIMIT = int(os.environ.get('HISTORY_LIMIT', '1000'))