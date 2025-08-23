from app.models.cliente_model import Cliente, Endereco, Telefone
from app import db

def listar_clientes():
    """
    Lista todos os clientes cadastrados.
    """
    clientes = Cliente.query.all()
    return clientes

def buscar_cliente_por_id(cliente_id):
    """
    Busca um cliente pelo seu ID.
    """
    cliente = Cliente.query.get(cliente_id)
    return cliente

def inserir_cliente(nome, cpf_cnpj=None, email=None):
    """
    Insere um novo cliente no banco de dados.
    """
    try:
        new_cliente = Cliente(nome=nome, cpf_cnpj=cpf_cnpj, email=email)
        db.session.add(new_cliente)
        db.session.commit()
        return new_cliente
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao inserir cliente: {e}")
        return None

def atualizar_cliente(cliente_id, nome=None, cpf_cnpj=None, email=None):
    """
    Atualiza as informações de um cliente existente.
    """
    cliente = Cliente.query.get(cliente_id)
    if cliente:
        if nome:
            cliente.nome = nome
        if cpf_cnpj:
            cliente.cpf_cnpj = cpf_cnpj
        if email:
            cliente.email = email
        try:
            db.session.commit()
            return cliente
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao atualizar cliente: {e}")
            return None
    return None

def excluir_cliente(cliente_id):
    """
    Exclui um cliente e seus dados relacionados (endereços, telefones, dispositivos, consumos).
    """
    cliente = Cliente.query.get(cliente_id)
    if cliente:
        try:
            db.session.delete(cliente)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao excluir cliente: {e}")
            return False
    return False

def adicionar_endereco_cliente(cliente_id, logradouro, numero=None, complemento=None, bairro=None, cidade=None, estado=None, cep=None, tipo_endereco='Instalacao'):
    """
    Adiciona um endereço a um cliente.
    """
    cliente = Cliente.query.get(cliente_id)
    if cliente:
        try:
            new_endereco = Endereco(
                cliente_id=cliente_id,
                logradouro=logradouro,
                numero=numero,
                complemento=complemento,
                bairro=bairro,
                cidade=cidade,
                estado=estado,
                cep=cep,
                tipo_endereco=tipo_endereco
            )
            db.session.add(new_endereco)
            db.session.commit()
            return new_endereco
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao adicionar endereço: {e}")
            return None
    return None

def buscar_endereco_por_id(endereco_id):
    """
    Busca um endereço pelo seu ID.
    """
    endereco = Endereco.query.get(endereco_id)
    return endereco

def excluir_endereco(endereco_id):
    """
    Exclui um endereço.
    """
    endereco = Endereco.query.get(endereco_id)
    if endereco:
        try:
            db.session.delete(endereco)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao excluir endereço: {e}")
            return False
    return False

def adicionar_telefone_cliente(cliente_id, numero, ddd=None, tipo_telefone='Celular'):
    """
    Adiciona um telefone a um cliente.
    """
    cliente = Cliente.query.get(cliente_id)
    if cliente:
        try:
            new_telefone = Telefone(
                cliente_id=cliente_id,
                ddd=ddd,
                numero=numero,
                tipo_telefone=tipo_telefone
            )
            db.session.add(new_telefone)
            db.session.commit()
            return new_telefone
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao adicionar telefone: {e}")
            return None
    return None

def buscar_telefone_por_id(telefone_id):
    """
    Busca um telefone pelo seu ID.
    """
    telefone = Telefone.query.get(telefone_id)
    return telefone

def excluir_telefone(telefone_id):
    """
    Exclui um telefone.
    """
    telefone = Telefone.query.get(telefone_id)
    if telefone:
        try:
            db.session.delete(telefone)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao excluir telefone: {e}")
            return False
    return False
