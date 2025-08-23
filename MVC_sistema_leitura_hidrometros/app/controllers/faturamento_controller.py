from app import app
from flask import render_template, request, redirect, url_for, flash
from app.services import faturamento_service, cliente_service # Importa cliente_service para dropdown de clientes
from app.models.faturamento_model import Tarifa, ConsumoMensal # Para uso nos templates
from datetime import datetime

# --- Rotas para Tarifas ---

@app.route('/tarifas')
def listar_tarifas():
    """
    Rota para exibir a lista de tarifas.
    """
    tarifas = faturamento_service.listar_tarifas()
    return render_template('tarifas.html', tarifas=tarifas)

@app.route('/tarifa/adicionar', methods=['GET', 'POST'])
def adicionar_tarifa():
    """
    Rota para adicionar uma nova tarifa.
    GET: Exibe o formulário de adição.
    POST: Processa os dados do formulário e adiciona a tarifa.
    """
    if request.method == 'POST':
        nome_tarifa = request.form['nome_tarifa']
        valor_m3 = request.form['valor_m3']
        data_inicio = datetime.strptime(request.form['data_inicio'], '%Y-%m-%d').date()
        data_fim = request.form.get('data_fim')
        if data_fim:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
        ativa = 'ativa' in request.form # Checkbox

        tarifa = faturamento_service.inserir_tarifa(nome_tarifa, float(valor_m3), data_inicio, data_fim, ativa)
        if tarifa:
            flash('Tarifa adicionada com sucesso!', 'success')
            return redirect(url_for('listar_tarifas'))
        else:
            flash('Erro ao adicionar tarifa. Verifique os dados.', 'danger')
    return render_template('adicionar_tarifa.html')

@app.route('/tarifa/editar/<int:tarifa_id>', methods=['GET', 'POST'])
def editar_tarifa(tarifa_id):
    """
    Rota para editar uma tarifa existente.
    GET: Exibe o formulário de edição com os dados atuais da tarifa.
    POST: Processa os dados do formulário e atualiza a tarifa.
    """
    tarifa = faturamento_service.buscar_tarifa_por_id(tarifa_id)
    if not tarifa:
        flash('Tarifa não encontrada.', 'danger')
        return redirect(url_for('listar_tarifas'))

    if request.method == 'POST':
        nome_tarifa = request.form['nome_tarifa']
        valor_m3 = request.form['valor_m3']
        data_inicio = datetime.strptime(request.form['data_inicio'], '%Y-%m-%d').date()
        data_fim = request.form.get('data_fim')
        if data_fim:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
        else:
            data_fim = None # Se o campo estiver vazio, definir como None
        ativa = 'ativa' in request.form

        updated_tarifa = faturamento_service.atualizar_tarifa(
            tarifa_id, nome_tarifa, float(valor_m3), data_inicio, data_fim, ativa
        )
        if updated_tarifa:
            flash('Tarifa atualizada com sucesso!', 'success')
            return redirect(url_for('listar_tarifas'))
        else:
            flash('Erro ao atualizar tarifa. Verifique os dados.', 'danger')
    return render_template('editar_tarifa.html', tarifa=tarifa)

@app.route('/tarifa/excluir/<int:tarifa_id>', methods=['POST'])
def excluir_tarifa(tarifa_id):
    """
    Rota para excluir uma tarifa.
    """
    if faturamento_service.excluir_tarifa(tarifa_id):
        flash('Tarifa excluída com sucesso!', 'success')
    else:
        flash('Erro ao excluir tarifa. Pode haver consumos mensais associados.', 'danger')
    return redirect(url_for('listar_tarifas'))

# --- Rotas para Consumo Mensal ---

@app.route('/consumos_mensais')
def listar_consumos_mensais():
    """
    Rota para exibir a lista de consumos mensais.
    """
    consumos = faturamento_service.listar_consumos_mensais()
    return render_template('consumos_mensais.html', consumos=consumos)

@app.route('/consumo_mensal/adicionar', methods=['GET', 'POST'])
def adicionar_consumo_mensal():
    """
    Rota para adicionar um novo registro de consumo mensal.
    GET: Exibe o formulário de adição.
    POST: Processa os dados do formulário e adiciona o consumo.
    """
    clientes = cliente_service.listar_clientes()
    tarifas = faturamento_service.listar_tarifas()

    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        mes_referencia = datetime.strptime(request.form['mes_referencia'], '%Y-%m-%d').date()
        litros_consumidos = float(request.form['litros_consumidos'])
        tarifa_aplicada_id = request.form.get('tarifa_aplicada_id')
        if tarifa_aplicada_id:
            tarifa_aplicada_id = int(tarifa_aplicada_id)

        # Calcular valor estimado se uma tarifa for selecionada
        valor_estimado = None
        if tarifa_aplicada_id:
            valor_estimado = faturamento_service.calcular_valor_estimado(litros_consumidos, tarifa_aplicada_id)

        consumo = faturamento_service.inserir_consumo_mensal(
            cliente_id, mes_referencia, litros_consumidos, valor_estimado, tarifa_aplicada_id
        )
        if consumo:
            flash('Consumo mensal adicionado com sucesso!', 'success')
            return redirect(url_for('listar_consumos_mensais'))
        else:
            flash('Erro ao adicionar consumo mensal. Verifique os dados.', 'danger')
    return render_template('adicionar_consumo_mensal.html', clientes=clientes, tarifas=tarifas)

@app.route('/consumo_mensal/editar/<int:consumo_id>', methods=['GET', 'POST'])
def editar_consumo_mensal(consumo_id):
    """
    Rota para editar um registro de consumo mensal existente.
    GET: Exibe o formulário de edição com os dados atuais.
    POST: Processa os dados do formulário e atualiza o consumo.
    """
    consumo = faturamento_service.buscar_consumo_mensal_por_id(consumo_id)
    if not consumo:
        flash('Consumo mensal não encontrado.', 'danger')
        return redirect(url_for('listar_consumos_mensais'))

    clientes = cliente_service.listar_clientes()
    tarifas = faturamento_service.listar_tarifas()

    if request.method == 'POST':
        litros_consumidos = float(request.form['litros_consumidos'])
        tarifa_aplicada_id = request.form.get('tarifa_aplicada_id')
        if tarifa_aplicada_id:
            tarifa_aplicada_id = int(tarifa_aplicada_id)
        else:
            tarifa_aplicada_id = None

        valor_estimado = None
        if tarifa_aplicada_id:
            valor_estimado = faturamento_service.calcular_valor_estimado(litros_consumidos, tarifa_aplicada_id)

        updated_consumo = faturamento_service.atualizar_consumo_mensal(
            consumo_id, litros_consumidos, valor_estimado, tarifa_aplicada_id
        )
        if updated_consumo:
            flash('Consumo mensal atualizado com sucesso!', 'success')
            return redirect(url_for('listar_consumos_mensais'))
        else:
            flash('Erro ao atualizar consumo mensal. Verifique os dados.', 'danger')
    return render_template('editar_consumo_mensal.html', consumo=consumo, clientes=clientes, tarifas=tarifas)

@app.route('/consumo_mensal/excluir/<int:consumo_id>', methods=['POST'])
def excluir_consumo_mensal(consumo_id):
    """
    Rota para excluir um registro de consumo mensal.
    """
    if faturamento_service.excluir_consumo_mensal(consumo_id):
        flash('Consumo mensal excluído com sucesso!', 'success')
    else:
        flash('Erro ao excluir consumo mensal.', 'danger')
    return redirect(url_for('listar_consumos_mensais'))

