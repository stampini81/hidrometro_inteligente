from app.models.dispositivo_model import Dispositivo, TipoDispositivo, Leitura, HistoricoStatusDispositivo
from app.models.cliente_model import Cliente # Para buscar clientes associados
from app import db
from datetime import datetime

def listar_dispositivos():
    """
    Lista todos os dispositivos cadastrados.
    """
    dispositivos = Dispositivo.query.all()
    return dispositivos

def buscar_dispositivo_por_id(dispositivo_id):
    """
    Busca um dispositivo pelo seu ID.
    """
    dispositivo = Dispositivo.query.get(dispositivo_id)
    return dispositivo

def inserir_dispositivo(modelo, numero_serie, cliente_id, tipo_dispositivo_id=None, data_instalacao=None, status='Ativo'):
    """
    Insere um novo dispositivo no banco de dados.
    """
    try:
        new_dispositivo = Dispositivo(
            modelo=modelo,
            numero_serie=numero_serie,
            cliente_id=cliente_id,
            tipo_dispositivo_id=tipo_dispositivo_id,
            data_instalacao=data_instalacao,
            status=status
        )
        db.session.add(new_dispositivo)
        db.session.commit()
        return new_dispositivo
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao inserir dispositivo: {e}")
        return None

def atualizar_dispositivo(dispositivo_id, modelo=None, numero_serie=None, cliente_id=None, tipo_dispositivo_id=None, data_instalacao=None, status=None):
    """
    Atualiza as informações de um dispositivo existente.
    """
    dispositivo = Dispositivo.query.get(dispositivo_id)
    if dispositivo:
        # Registra o histórico de status se houver mudança
        if status and dispositivo.status != status:
            historico_status = HistoricoStatusDispositivo(
                dispositivo_id=dispositivo.id_dispositivo,
                status_anterior=dispositivo.status,
                status_novo=status,
                data_alteracao=datetime.now()
            )
            db.session.add(historico_status)

        if modelo:
            dispositivo.modelo = modelo
        if numero_serie:
            dispositivo.numero_serie = numero_serie
        if cliente_id:
            dispositivo.cliente_id = cliente_id
        if tipo_dispositivo_id:
            dispositivo.tipo_dispositivo_id = tipo_dispositivo_id
        if data_instalacao:
            dispositivo.data_instalacao = data_instalacao
        if status:
            dispositivo.status = status

        try:
            db.session.commit()
            return dispositivo
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao atualizar dispositivo: {e}")
            return None
    return None

def excluir_dispositivo(dispositivo_id):
    """
    Exclui um dispositivo e suas leituras e histórico de status relacionados.
    """
    dispositivo = Dispositivo.query.get(dispositivo_id)
    if dispositivo:
        try:
            db.session.delete(dispositivo)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao excluir dispositivo: {e}")
            return False
    return False

def adicionar_tipo_dispositivo(nome_tipo, descricao=None):
    """
    Adiciona um novo tipo de dispositivo.
    """
    try:
        new_tipo = TipoDispositivo(nome_tipo=nome_tipo, descricao=descricao)
        db.session.add(new_tipo)
        db.session.commit()
        return new_tipo
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao adicionar tipo de dispositivo: {e}")
        return None

def listar_tipos_dispositivo():
    """
    Lista todos os tipos de dispositivo.
    """
    tipos = TipoDispositivo.query.all()
    return tipos

def registrar_leitura(dispositivo_id, consumo_litros, bateria=None, pressao_bar=None, vazamento_detectado=False):
    """
    Registra uma nova leitura para um dispositivo.
    """
    dispositivo = Dispositivo.query.get(dispositivo_id)
    if dispositivo:
        try:
            new_leitura = Leitura(
                dispositivo_id=dispositivo_id,
                data_hora=datetime.now(),
                consumo_litros=consumo_litros,
                bateria=bateria,
                pressao_bar=pressao_bar,
                vazamento_detectado=vazamento_detectado
            )
            db.session.add(new_leitura)
            db.session.commit()
            return new_leitura
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao registrar leitura: {e}")
            return None
    return None

def listar_leituras_por_dispositivo(dispositivo_id):
    """
    Lista todas as leituras para um dispositivo específico.
    """
    leituras = Leitura.query.filter_by(dispositivo_id=dispositivo_id).order_by(Leitura.data_hora.desc()).all()
    return leituras

