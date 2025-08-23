from app import app
from flask import render_template, request, redirect, url_for, flash, jsonify
from app.services import dispositivo_service, cliente_service # Importa cliente_service para listar clientes
from app.models.dispositivo_model import Dispositivo # Importa o modelo Dispositivo para uso no template
from app.models.dispositivo_model import Leitura
from app import db

@app.route('/api/clientes/<int:cliente_id>/dispositivos/current')
def api_cliente_dispositivos_current(cliente_id):
    """Retorna para cada dispositivo do cliente a última leitura (se houver)."""
    cliente = cliente_service.buscar_cliente_por_id(cliente_id) if hasattr(cliente_service, 'buscar_cliente_por_id') else None
    if not cliente:
        return jsonify({'error': 'cliente_not_found'}), 404
    dispositivos = Dispositivo.query.filter_by(cliente_id=cliente_id).all()
    result = []
    for d in dispositivos:
        leitura = (Leitura.query.filter_by(dispositivo_id=d.id_dispositivo)
                   .order_by(Leitura.data_hora.desc()).first())
        result.append({
            'dispositivo_id': d.id_dispositivo,
            'numero_serie': d.numero_serie,
            'modelo': d.modelo,
            'status': d.status,
            'ultima_leitura': {
                'data_hora': leitura.data_hora.isoformat() if leitura else None,
                'consumo_litros': float(leitura.consumo_litros) if leitura and leitura.consumo_litros is not None else None,
                'total_liters': float(leitura.total_liters) if leitura and leitura.total_liters is not None else None,
                'flow_lmin': float(leitura.flow_lmin) if leitura and leitura.flow_lmin is not None else None,
            } if leitura else None
        })
    return jsonify({'cliente_id': cliente_id, 'dispositivos': result})

@app.route('/dispositivos')
def listar_dispositivos():
    """
    Rota para exibir a lista de dispositivos.
    """
    dispositivos = dispositivo_service.listar_dispositivos()
    return render_template('dispositivos.html', dispositivos=dispositivos)

@app.route('/dispositivo/adicionar', methods=['GET', 'POST'])
def adicionar_dispositivo():
    """
    Rota para adicionar um novo dispositivo.
    GET: Exibe o formulário de adição.
    POST: Processa os dados do formulário e adiciona o dispositivo.
    """
    clientes = cliente_service.listar_clientes() # Para o dropdown de seleção de cliente
    tipos_dispositivo = dispositivo_service.listar_tipos_dispositivo() # Para o dropdown de seleção de tipo

    if request.method == 'POST':
        modelo = request.form['modelo']
        numero_serie = request.form['numero_serie']
        cliente_id = request.form['cliente_id']
        tipo_dispositivo_id = request.form.get('tipo_dispositivo_id')
        data_instalacao = request.form.get('data_instalacao')
        status = request.form.get('status', 'Ativo')

        dispositivo = dispositivo_service.inserir_dispositivo(
            modelo, numero_serie, cliente_id, tipo_dispositivo_id, data_instalacao, status
        )
        if dispositivo:
            flash('Dispositivo adicionado com sucesso!', 'success')
            return redirect(url_for('listar_dispositivos'))
        else:
            flash('Erro ao adicionar dispositivo. Verifique os dados.', 'danger')
    return render_template('adicionar_dispositivo.html', clientes=clientes, tipos_dispositivo=tipos_dispositivo) # Você precisará criar este template

@app.route('/dispositivo/editar/<int:dispositivo_id>', methods=['GET', 'POST'])
def editar_dispositivo(dispositivo_id):
    """
    Rota para editar um dispositivo existente.
    GET: Exibe o formulário de edição com os dados atuais do dispositivo.
    POST: Processa os dados do formulário e atualiza o dispositivo.
    """
    dispositivo = dispositivo_service.buscar_dispositivo_por_id(dispositivo_id)
    if not dispositivo:
        flash('Dispositivo não encontrado.', 'danger')
        return redirect(url_for('listar_dispositivos'))

    clientes = cliente_service.listar_clientes()
    tipos_dispositivo = dispositivo_service.listar_tipos_dispositivo()

    if request.method == 'POST':
        modelo = request.form['modelo']
        numero_serie = request.form['numero_serie']
        cliente_id = request.form['cliente_id']
        tipo_dispositivo_id = request.form.get('tipo_dispositivo_id')
        data_instalacao = request.form.get('data_instalacao')
        status = request.form.get('status')

        updated_dispositivo = dispositivo_service.atualizar_dispositivo(
            dispositivo_id, modelo, numero_serie, cliente_id, tipo_dispositivo_id, data_instalacao, status
        )
        if updated_dispositivo:
            flash('Dispositivo atualizado com sucesso!', 'success')
            return redirect(url_for('listar_dispositivos'))
        else:
            flash('Erro ao atualizar dispositivo. Verifique os dados.', 'danger')
    return render_template('editar_dispositivo.html', dispositivo=dispositivo, clientes=clientes, tipos_dispositivo=tipos_dispositivo) # Você precisará criar este template

@app.route('/dispositivo/excluir/<int:dispositivo_id>', methods=['POST'])
def excluir_dispositivo(dispositivo_id):
    """
    Rota para excluir um dispositivo.
    """
    if dispositivo_service.excluir_dispositivo(dispositivo_id):
        flash('Dispositivo excluído com sucesso!', 'success')
    else:
        flash('Erro ao excluir dispositivo. Pode haver leituras ou histórico associados.', 'danger')
    return redirect(url_for('listar_dispositivos'))

@app.route('/dispositivo/leitura/<int:dispositivo_id>', methods=['GET', 'POST'])
def registrar_leitura(dispositivo_id):
    """
    Rota para registrar uma nova leitura para um dispositivo.
    GET: Exibe o formulário de registro de leitura.
    POST: Processa os dados do formulário e registra a leitura.
    """
    dispositivo = dispositivo_service.buscar_dispositivo_por_id(dispositivo_id)
    if not dispositivo:
        flash('Dispositivo não encontrado.', 'danger')
        return redirect(url_for('listar_dispositivos'))

    if request.method == 'POST':
        consumo_litros = request.form['consumo_litros']
        bateria = request.form.get('bateria')
        pressao_bar = request.form.get('pressao_bar')
        vazamento_detectado = 'vazamento_detectado' in request.form # Checkbox

        leitura = dispositivo_service.registrar_leitura(
            dispositivo_id, consumo_litros, bateria, pressao_bar, vazamento_detectado
        )
        if leitura:
            flash('Leitura registrada com sucesso!', 'success')
            return redirect(url_for('listar_leituras_dispositivo', dispositivo_id=dispositivo_id))
        else:
            flash('Erro ao registrar leitura. Verifique os dados.', 'danger')
    return render_template('registrar_leitura.html', dispositivo=dispositivo) # Você precisará criar este template

@app.route('/dispositivo/leituras/<int:dispositivo_id>')
def listar_leituras_dispositivo(dispositivo_id):
    """
    Rota para exibir as leituras de um dispositivo específico.
    """
    dispositivo = dispositivo_service.buscar_dispositivo_por_id(dispositivo_id)
    if not dispositivo:
        flash('Dispositivo não encontrado.', 'danger')
        return redirect(url_for('listar_dispositivos'))

    leituras = dispositivo_service.listar_leituras_por_dispositivo(dispositivo_id)
    return render_template('leituras_dispositivo.html', dispositivo=dispositivo, leituras=leituras)

