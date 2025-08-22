from app import app
from flask import render_template, request, redirect, url_for, flash
from app.services import dispositivo_service # Reutilizamos o serviço de dispositivo para gerenciar tipos

@app.route('/tipos_dispositivo')
def listar_tipos_dispositivo():
    """
    Rota para exibir a lista de tipos de dispositivo.
    """
    tipos = dispositivo_service.listar_tipos_dispositivo()
    return render_template('tipos_dispositivo.html', tipos=tipos)

@app.route('/tipo_dispositivo/adicionar', methods=['GET', 'POST'])
def adicionar_tipo_dispositivo():
    """
    Rota para adicionar um novo tipo de dispositivo.
    GET: Exibe o formulário de adição.
    POST: Processa os dados do formulário e adiciona o tipo.
    """
    if request.method == 'POST':
        nome_tipo = request.form['nome_tipo']
        descricao = request.form.get('descricao')

        tipo = dispositivo_service.adicionar_tipo_dispositivo(nome_tipo, descricao)
        if tipo:
            flash('Tipo de dispositivo adicionado com sucesso!', 'success')
            return redirect(url_for('listar_tipos_dispositivo'))
        else:
            flash('Erro ao adicionar tipo de dispositivo. Verifique os dados.', 'danger')
    return render_template('adicionar_tipo_dispositivo.html')

