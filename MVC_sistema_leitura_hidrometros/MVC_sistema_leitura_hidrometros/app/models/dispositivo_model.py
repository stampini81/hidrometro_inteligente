from app import db
from sqlalchemy.dialects.mysql import ENUM # Importa ENUM para MySQL, se necessário

class TipoDispositivo(db.Model):
    """
    Modelo para a tabela 'TipoDispositivo'.
    Define os tipos de dispositivos (ex: Hidrômetro Residencial, Hidrômetro Industrial).
    """
    __tablename__ = "TipoDispositivo"

    id_tipo_dispositivo = db.Column(db.Integer, primary_key=True)
    nome_tipo = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text)

    # Relacionamento: Um tipo de dispositivo pode ter vários dispositivos
    dispositivos = db.relationship('Dispositivo', backref='tipo_dispositivo', lazy=True)

    def __repr__(self):
        return f'<TipoDispositivo {self.nome_tipo}>'

class Dispositivo(db.Model):
    """
    Modelo para a tabela 'Dispositivo'.
    Armazena informações sobre os dispositivos (hidrômetros ou outros sensores).
    """
    __tablename__ = "Dispositivo"

    id_dispositivo = db.Column(db.Integer, primary_key=True)
    modelo = db.Column(db.String(100), nullable=False)
    numero_serie = db.Column(db.String(100), unique=True, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('Cliente.id_cliente'), nullable=False)
    tipo_dispositivo_id = db.Column(db.Integer, db.ForeignKey('TipoDispositivo.id_tipo_dispositivo'))
    data_instalacao = db.Column(db.Date)
    # Para SQLite, ENUM não é nativamente suportado como no MySQL.
    # Uma abordagem comum é usar String e validar no código ou usar um tipo customizado.
    # Para compatibilidade, usaremos String e lista de valores permitidos.
    status = db.Column(db.String(50), default='Ativo') # ENUM('Ativo', 'Inativo', 'Manutencao', 'Defeito')

    # Relacionamentos:
    # Um dispositivo pode ter várias leituras
    leituras = db.relationship('Leitura', backref='dispositivo', lazy=True, cascade="all, delete-orphan")
    # Um dispositivo pode ter um histórico de status
    historico_status = db.relationship('HistoricoStatusDispositivo', backref='dispositivo', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Dispositivo {self.numero_serie} - Modelo: {self.modelo}>'

class Leitura(db.Model):
    """
    Modelo para a tabela 'Leitura'.
    Armazena as leituras de consumo dos dispositivos.
    """
    __tablename__ = "Leitura"

    id_leitura = db.Column(db.Integer, primary_key=True)
    dispositivo_id = db.Column(db.Integer, db.ForeignKey('Dispositivo.id_dispositivo'), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False)
    consumo_litros = db.Column(db.Numeric(10, 2), nullable=False)
    bateria = db.Column(db.Numeric(5, 2))
    pressao_bar = db.Column(db.Numeric(5, 2))
    vazamento_detectado = db.Column(db.Boolean, default=False)
    total_liters = db.Column(db.Numeric(12, 3))  # novo campo acumulado total de litros
    flow_lmin = db.Column(db.Numeric(10, 3))     # novo campo vazão instantânea L/min

    def __repr__(self):
        return f'<Leitura ID: {self.id_leitura} - Dispositivo: {self.dispositivo_id} - Consumo: {self.consumo_litros}>'

class HistoricoStatusDispositivo(db.Model):
    """
    Modelo para a tabela 'HistoricoStatusDispositivo'.
    Registra o histórico de mudanças de status de um dispositivo.
    """
    __tablename__ = "HistoricoStatusDispositivo"

    id_historico = db.Column(db.Integer, primary_key=True)
    dispositivo_id = db.Column(db.Integer, db.ForeignKey('Dispositivo.id_dispositivo'), nullable=False)
    status_anterior = db.Column(db.String(50)) # ENUM('Ativo', 'Inativo', 'Manutencao', 'Defeito')
    status_novo = db.Column(db.String(50), nullable=False) # ENUM('Ativo', 'Inativo', 'Manutencao', 'Defeito')
    data_alteracao = db.Column(db.DateTime, default=db.func.current_timestamp())
    observacoes = db.Column(db.Text)

    def __repr__(self):
        return f'<HistoricoStatusDispositivo ID: {self.id_historico} - Dispositivo: {self.dispositivo_id} - Status Novo: {self.status_novo}>'

