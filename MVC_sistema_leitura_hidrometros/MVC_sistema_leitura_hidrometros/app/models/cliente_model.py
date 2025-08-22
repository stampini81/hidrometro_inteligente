from app import db

class Cliente(db.Model):
    """
    Modelo para a tabela 'Cliente'.
    Armazena informações dos clientes.
    """
    __tablename__ = "Cliente"

    id_cliente = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf_cnpj = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(100))
    data_cadastro = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relacionamentos
    # Um cliente pode ter vários endereços
    enderecos = db.relationship('Endereco', backref='cliente', lazy=True, cascade="all, delete-orphan")
    # Um cliente pode ter vários telefones
    telefones = db.relationship('Telefone', backref='cliente', lazy=True, cascade="all, delete-orphan")
    # Um cliente pode ter vários dispositivos
    dispositivos = db.relationship('Dispositivo', backref='cliente', lazy=True, cascade="all, delete-orphan")
    # Um cliente pode ter vários registros de consumo mensal
    consumos_mensais = db.relationship('ConsumoMensal', backref='cliente', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Cliente {self.nome}>'

class Endereco(db.Model):
    """
    Modelo para a tabela 'Endereco'.
    Armazena os endereços dos clientes.
    """
    __tablename__ = "Endereco"

    id_endereco = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('Cliente.id_cliente'), nullable=False)
    tipo_endereco = db.Column(db.String(50), default='Instalacao')
    logradouro = db.Column(db.String(255), nullable=False)
    numero = db.Column(db.String(20))
    complemento = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(2), nullable=False)
    cep = db.Column(db.String(10))

    def __repr__(self):
        return f'<Endereco {self.logradouro}, {self.numero} - Cliente ID: {self.cliente_id}>'

class Telefone(db.Model):
    """
    Modelo para a tabela 'Telefone'.
    Armazena os telefones dos clientes.
    """
    __tablename__ = "Telefone"

    id_telefone = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('Cliente.id_cliente'), nullable=False)
    ddd = db.Column(db.String(5))
    numero = db.Column(db.String(15), nullable=False)
    tipo_telefone = db.Column(db.String(50), default='Celular')

    def __repr__(self):
        return f'<Telefone ({self.ddd}) {self.numero} - Cliente ID: {self.cliente_id}>'

