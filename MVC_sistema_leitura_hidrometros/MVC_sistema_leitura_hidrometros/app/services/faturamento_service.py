from app.models.faturamento_model import Tarifa, ConsumoMensal
from app.models.cliente_model import Cliente # Para relacionamentos e busca de clientes
from app import db
from datetime import datetime
from sqlalchemy import func
from decimal import Decimal # Importar o tipo Decimal

def listar_tarifas():
    """
    Lista todas as tarifas cadastradas.
    """
    tarifas = Tarifa.query.all()
    return tarifas

def buscar_tarifa_por_id(tarifa_id):
    """
    Busca uma tarifa pelo seu ID.
    """
    tarifa = Tarifa.query.get(tarifa_id)
    return tarifa

def inserir_tarifa(nome_tarifa, valor_m3, data_inicio, data_fim=None, ativa=True):
    """
    Insere uma nova tarifa no banco de dados.
    """
    try:
        new_tarifa = Tarifa(
            nome_tarifa=nome_tarifa,
            valor_m3=valor_m3,
            data_inicio=data_inicio,
            data_fim=data_fim,
            ativa=ativa
        )
        db.session.add(new_tarifa)
        db.session.commit()
        return new_tarifa
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao inserir tarifa: {e}")
        return None

def atualizar_tarifa(tarifa_id, nome_tarifa=None, valor_m3=None, data_inicio=None, data_fim=None, ativa=None):
    """
    Atualiza as informações de uma tarifa existente.
    """
    tarifa = Tarifa.query.get(tarifa_id)
    if tarifa:
        if nome_tarifa:
            tarifa.nome_tarifa = nome_tarifa
        if valor_m3:
            tarifa.valor_m3 = valor_m3
        if data_inicio:
            tarifa.data_inicio = data_inicio
        if data_fim:
            tarifa.data_fim = data_fim
        if ativa is not None:
            tarifa.ativa = ativa
        try:
            db.session.commit()
            return tarifa
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao atualizar tarifa: {e}")
            return None
    return None

def excluir_tarifa(tarifa_id):
    """
    Exclui uma tarifa.
    """
    tarifa = Tarifa.query.get(tarifa_id)
    if tarifa:
        try:
            db.session.delete(tarifa)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao excluir tarifa: {e}")
            return False
    return False

def listar_consumos_mensais():
    """
    Lista todos os registros de consumo mensal.
    """
    consumos = ConsumoMensal.query.all()
    return consumos

def buscar_consumo_mensal_por_id(consumo_id):
    """
    Busca um registro de consumo mensal pelo seu ID.
    """
    consumo = ConsumoMensal.query.get(consumo_id)
    return consumo

def inserir_consumo_mensal(cliente_id, mes_referencia, litros_consumidos, valor_estimado=None, tarifa_aplicada_id=None):
    """
    Insere um novo registro de consumo mensal.
    """
    try:
        new_consumo = ConsumoMensal(
            cliente_id=cliente_id,
            mes_referencia=mes_referencia,
            litros_consumidos=litros_consumidos,
            valor_estimado=valor_estimado,
            tarifa_aplicada_id=tarifa_aplicada_id
        )
        db.session.add(new_consumo)
        db.session.commit()
        return new_consumo
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao inserir consumo mensal: {e}")
        return None

def atualizar_consumo_mensal(consumo_id, litros_consumidos=None, valor_estimado=None, tarifa_aplicada_id=None):
    """
    Atualiza um registro de consumo mensal existente.
    """
    consumo = ConsumoMensal.query.get(consumo_id)
    if consumo:
        if litros_consumidos:
            consumo.litros_consumidos = litros_consumidos
        if valor_estimado:
            consumo.valor_estimado = valor_estimado
        if tarifa_aplicada_id:
            consumo.tarifa_aplicada_id = tarifa_aplicada_id
        try:
            db.session.commit()
            return consumo
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao atualizar consumo mensal: {e}")
            return None
    return None

def excluir_consumo_mensal(consumo_id):
    """
    Exclui um registro de consumo mensal.
    """
    consumo = ConsumoMensal.query.get(consumo_id)
    if consumo:
        try:
            db.session.delete(consumo)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao excluir consumo mensal: {e}")
            return False
    return False

def calcular_valor_estimado(litros_consumidos, tarifa_id):
    """
    Calcula o valor estimado com base no consumo em litros e na tarifa.
    Converte litros para m³ e aplica a tarifa.
    """
    tarifa = Tarifa.query.get(tarifa_id)
    if tarifa and tarifa.ativa:
        # Converte litros_consumidos para Decimal antes da operação
        consumo_m3 = Decimal(str(litros_consumidos)) / Decimal('1000.0')
        valor_estimado = consumo_m3 * tarifa.valor_m3
        return round(valor_estimado, 2)
    return None

