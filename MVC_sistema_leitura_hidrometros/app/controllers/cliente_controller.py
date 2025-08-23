from app import app, login_required_view
from flask import render_template, request, redirect, url_for, flash
from app.services import cliente_service
from app.models.cliente_model import Cliente, Endereco, Telefone  # Importa os modelos Endereco e Telefone


@app.route('/')
@app.route('/clientes')
@login_required_view
def listar_clientes():
    """
    Rota para exibir a lista de clientes.
    """
    clientes = cliente_service.listar_clientes()
    return render_template('clientes.html', clientes=clientes)


@app.route('/cliente/adicionar', methods=['GET', 'POST'])
@login_required_view
def adicionar_cliente():
    """
    Rota para adicionar um novo cliente.
    GET: Exibe o formulário de adição.
    POST: Processa os dados do formulário e adiciona o cliente.
    """
    if request.method == 'POST':
        nome = request.form['nome']
        cpf_cnpj = request.form.get('cpf_cnpj')
        email = request.form.get('email')

        cliente = cliente_service.inserir_cliente(nome, cpf_cnpj, email)
        if cliente:
            flash('Cliente adicionado com sucesso!', 'success')
            return redirect(url_for('listar_clientes'))
        else:
            flash('Erro ao adicionar cliente. Verifique os dados.', 'danger')
    return render_template('adicionar_cliente.html')


@app.route('/cliente/editar/<int:cliente_id>', methods=['GET', 'POST'])
@login_required_view
def editar_cliente(cliente_id):
    """
    Rota para editar um cliente existente.
    GET: Exibe o formulário de edição com os dados atuais do cliente.
    POST: Processa os dados do formulário e atualiza o cliente.
    """
    cliente = cliente_service.buscar_cliente_por_id(cliente_id)
    if not cliente:
        flash('Cliente não encontrado.', 'danger')
        return redirect(url_for('listar_clientes'))

    if request.method == 'POST':
        nome = request.form['nome']
        cpf_cnpj = request.form.get('cpf_cnpj')
        email = request.form.get('email')

        updated_cliente = cliente_service.atualizar_cliente(cliente_id, nome, cpf_cnpj, email)
        if updated_cliente:
            flash('Cliente atualizado com sucesso!', 'success')
            return redirect(url_for('listar_clientes'))
        else:
            flash('Erro ao atualizar cliente. Verifique os dados.', 'danger')
    return render_template('editar_cliente.html', cliente=cliente)


@app.route('/cliente/excluir/<int:cliente_id>', methods=['POST'])
@login_required_view
def excluir_cliente(cliente_id):
    """
    Rota para excluir um cliente.
    """
    if cliente_service.excluir_cliente(cliente_id):
        flash('Cliente excluído com sucesso!', 'success')
    else:
        flash('Erro ao excluir cliente. Pode haver dispositivos ou leituras associadas.', 'danger')
    return redirect(url_for('listar_clientes'))


# --- Novas Rotas para Detalhes, Endereços e Telefones ---

@app.route('/cliente/detalhes/<int:cliente_id>', methods=['GET'])
@login_required_view
def detalhes_cliente(cliente_id):
    """
    Rota para exibir os detalhes de um cliente, incluindo seus endereços e telefones.
    """
    cliente = cliente_service.buscar_cliente_por_id(cliente_id)
    if not cliente:
        flash('Cliente não encontrado.', 'danger')
        return redirect(url_for('listar_clientes'))

    # Flask-SQLAlchemy carrega os relacionamentos 'enderecos' e 'telefones' automaticamente
    # porque lazy=True está definido nos modelos.
    return render_template('detalhes_cliente.html', cliente=cliente)


@app.route('/cliente/<int:cliente_id>/endereco/adicionar', methods=['GET', 'POST'])
@login_required_view
def adicionar_endereco(cliente_id):
    """
    Rota para adicionar um novo endereço a um cliente.
    GET: Exibe o formulário de adição.
    POST: Processa os dados do formulário e adiciona o endereço.
    """
    cliente = cliente_service.buscar_cliente_por_id(cliente_id)
    if not cliente:
        flash('Cliente não encontrado.', 'danger')
        return redirect(url_for('listar_clientes'))

    if request.method == 'POST':
        logradouro = request.form['logradouro']
        numero = request.form.get('numero')
        complemento = request.form.get('complemento')
        bairro = request.form.get('bairro')
        cidade = request.form['cidade']
        estado = request.form['estado']
        cep = request.form.get('cep')
        tipo_endereco = request.form.get('tipo_endereco', 'Instalacao')

        endereco = cliente_service.adicionar_endereco_cliente(
            cliente_id, logradouro, numero, complemento, bairro, cidade, estado, cep, tipo_endereco
        )
        if endereco:
            flash('Endereço adicionado com sucesso!', 'success')
            return redirect(url_for('detalhes_cliente', cliente_id=cliente_id))
        else:
            flash('Erro ao adicionar endereço. Verifique os dados.', 'danger')
    return render_template('adicionar_endereco.html', cliente=cliente)


@app.route('/cliente/<int:cliente_id>/endereco/excluir/<int:endereco_id>', methods=['POST'])
@login_required_view
def excluir_endereco(cliente_id, endereco_id):
    """
    Rota para excluir um endereço de um cliente.
    """
    if cliente_service.excluir_endereco(endereco_id):  # Você precisará adicionar esta função ao service
        flash('Endereço excluído com sucesso!', 'success')
    else:
        flash('Erro ao excluir endereço.', 'danger')
    return redirect(url_for('detalhes_cliente', cliente_id=cliente_id))


@app.route('/cliente/<int:cliente_id>/telefone/adicionar', methods=['GET', 'POST'])
@login_required_view
def adicionar_telefone(cliente_id):
    """
    Rota para adicionar um novo telefone a um cliente.
    GET: Exibe o formulário de adição.
    POST: Processa os dados do formulário e adiciona o telefone.
    """
    cliente = cliente_service.buscar_cliente_por_id(cliente_id)
    if not cliente:
        flash('Cliente não encontrado.', 'danger')
        return redirect(url_for('listar_clientes'))

    if request.method == 'POST':
        ddd = request.form.get('ddd')
        numero = request.form['numero']
        tipo_telefone = request.form.get('tipo_telefone', 'Celular')

        telefone = cliente_service.adicionar_telefone_cliente(
            cliente_id, numero, ddd, tipo_telefone
        )
        if telefone:
            flash('Telefone adicionado com sucesso!', 'success')
            return redirect(url_for('detalhes_cliente', cliente_id=cliente_id))
        else:
            flash('Erro ao adicionar telefone. Verifique os dados.', 'danger')
    return render_template('adicionar_telefone.html', cliente=cliente)


@app.route('/cliente/<int:cliente_id>/telefone/excluir/<int:telefone_id>', methods=['POST'])
@login_required_view
def excluir_telefone(cliente_id, telefone_id):
    """
    Rota para excluir um telefone de um cliente.
    """
    if cliente_service.excluir_telefone(telefone_id):  # Você precisará adicionar esta função ao service
        flash('Telefone excluído com sucesso!', 'success')
    else:
        flash('Erro ao excluir telefone.', 'danger')
    return redirect(url_for('detalhes_cliente', cliente_id=cliente_id))


@app.route('/dashboard', endpoint='dashboard')
@login_required_view
def dashboard():
    return render_template('dashboard.html')

@app.route('/control', endpoint='control')
@login_required_view
def control():
    return render_template('control.html')

@app.route('/cliente/<int:cliente_id>/tempo-real')
@login_required_view
def cliente_tempo_real(cliente_id):
    cliente = cliente_service.buscar_cliente_por_id(cliente_id)
    if not cliente:
        flash('Cliente não encontrado.', 'danger')
        return redirect(url_for('listar_clientes'))
    return render_template('cliente_tempo_real.html', cliente=cliente)
