from app import db

class Tarifa(db.Model):
    """
    Modelo para a tabela 'Tarifa'.
    Armazena as diferentes tarifas de consumo aplicadas.
    """
    __tablename__ = "Tarifa"

    id_tarifa = db.Column(db.Integer, primary_key=True)
    nome_tarifa = db.Column(db.String(100), nullable=False)
    valor_m3 = db.Column(db.Numeric(10, 2), nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date)
    ativa = db.Column(db.Boolean, default=True)

    # Não há relacionamento direto 'many-to-one' aqui que precise de backref simples.
    # A Tarifa é referenciada por ConsumoMensal.

    def __repr__(self):
        return f'<Tarifa {self.nome_tarifa} - R${self.valor_m3}/m³>'

class ConsumoMensal(db.Model):
    """
    Modelo para a tabela 'ConsumoMensal'.
    Armazena o consumo mensal consolidado por cliente.
    """
    __tablename__ = "ConsumoMensal"

    id_consumo = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('Cliente.id_cliente'), nullable=False)
    mes_referencia = db.Column(db.Date, nullable=False)
    litros_consumidos = db.Column(db.Numeric(10, 2), nullable=False)
    valor_estimado = db.Column(db.Numeric(10, 2))
    tarifa_aplicada_id = db.Column(db.Integer, db.ForeignKey('Tarifa.id_tarifa'))

    # Relacionamentos
    # Um consumo mensal pertence a uma tarifa específica
    tarifa_aplicada = db.relationship('Tarifa', backref='consumos_mensais', lazy=True)

    def __repr__(self):
        return f'<ConsumoMensal Cliente:{self.cliente_id} Mês:{self.mes_referencia} Litros:{self.litros_consumidos}>'

