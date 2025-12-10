from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.models import Usuario, Solicitacao
from sqlalchemy.exc import IntegrityError
from datetime import datetime


print("--- ROTAS CARREGADAS COM SUCESSO ---")

bp = Blueprint('main', __name__)
@bp.app_template_filter('datetimeformat')
def datetimeformat(value, format='%d-%m-%y'):
    try:
        # tenta converter string do tipo "2025-12-09"
        return datetime.strptime(value, "%Y-%m-%d").strftime(format)
    except:
        return value  # se falhar, retorna como está
# --- Context Processor: Simula o 'current_user' para o HTML ---
@bp.context_processor
def inject_user():
    class MockUser:
        is_authenticated = 'user_id' in session
        name = session.get('user_nome')
        id = session.get('user_id')
        role = session.get('user_tipo')
    return dict(current_user=MockUser())

# --- DASHBOARD UVIS ---

@bp.route('/')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    if session.get('user_tipo') == 'admin':
        return redirect(url_for('main.admin_dashboard'))

    user_id = int(session.get('user_id'))
    
    # Filtros
    query = Solicitacao.query.filter_by(usuario_id=user_id)
    filtro_status = request.args.get('status')
    if filtro_status:
        query = query.filter(Solicitacao.status == filtro_status)

    # Paginação (igual ao Admin)
    page = request.args.get('page', 1, type=int)
    paginacao = query.order_by(Solicitacao.data_criacao.desc()).paginate(page=page, per_page=10)
    
    return render_template(
        'dashboard.html', 
        nome=session.get('user_nome'), 
        solicitacoes=paginacao.items,  # Lista de pedidos da página atual
        paginacao=paginacao            # Objeto para criar os botões Próximo/Anterior
    )

# --- PAINEL ADMIN (com filtros) ---
@bp.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('user_tipo') != 'admin':
        return redirect(url_for('main.login'))
    
    # --- Captura filtros enviados pelo GET ---
    filtro_status = request.args.get("status")
    filtro_unidade = request.args.get("unidade")
    filtro_regiao = request.args.get("regiao")

    # --- Query base ---
    query = Solicitacao.query.join(Usuario)

    # --- Filtros aplicáveis ---
    if filtro_status:
        query = query.filter(Solicitacao.status == filtro_status)

    if filtro_unidade:
        query = query.filter(Usuario.nome_uvis.ilike(f"%{filtro_unidade}%"))

    if filtro_regiao:
        query = query.filter(Usuario.regiao.ilike(f"%{filtro_regiao}%"))

    page = request.args.get("page", 1, type=int)

    paginacao = query.order_by(
    Solicitacao.data_criacao.desc()
    ).paginate(page=page, per_page=9)

    return render_template(
    'admin.html',
    pedidos=paginacao.items,
    paginacao=paginacao
)

@bp.route('/admin/exportar_excel')
def exportar_excel():
    if 'user_id' not in session or session.get('user_tipo') != 'admin':
        return redirect(url_for('main.login'))

    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
    from io import BytesIO
    from flask import send_file

    # Filtros (Mantidos)
    filtro_status = request.args.get("status")
    filtro_unidade = request.args.get("unidade")
    filtro_regiao = request.args.get("regiao")

    query = Solicitacao.query.join(Usuario)

    if filtro_status:
        query = query.filter(Solicitacao.status == filtro_status)
    if filtro_unidade:
        query = query.filter(Usuario.nome_uvis.ilike(f"%{filtro_unidade}%"))
    if filtro_regiao:
        query = query.filter(Usuario.regiao.ilike(f"%{filtro_regiao}%"))

    pedidos = query.order_by(Solicitacao.data_criacao.desc()).all()

    # --- EXCEL ---
    wb = Workbook()
    ws = wb.active
    ws.title = "Relatório Completo"

    # CABEÇALHO ATUALIZADO
    headers = [
        "ID", "Unidade", "Região", 
        "Data Agendada", "Hora", 
        "CEP", "Endereço", "Bairro", "Cidade",
        "Latitude", "Longitude",
        "Foco", "Tipo Visita", "Altura", "Criadouro?", "Apoio CET?", 
        "Observação",
        "Status", "Protocolo", "Justificativa Recusa"
    ]

    # Estilos (Mantidos)
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # DADOS
    row_num = 2
    for p in pedidos:
        # Formatação de Endereço
        compl = f" ({p.complemento})" if p.complemento else ""
        end_completo = f"{p.logradouro}, {p.numero or 'S/N'}{compl}"

        # Tratamento de Booleans (Sim/Não)
        criadouro_txt = "SIM" if p.criadouro else "NÃO"
        cet_txt = "SIM" if p.apoio_cet else "NÃO"

        row = [
            p.id,
            p.autor.nome_uvis,
            p.autor.regiao,
            p.data_agendamento, # O Excel entende objeto Date do Python automaticamente
            p.hora_agendamento,
            p.cep,
            end_completo,
            p.bairro,
            f"{p.cidade}/{p.uf}",
            p.latitude,
            p.longitude,
            p.foco,
            p.tipo_visita,
            p.altura_voo,
            criadouro_txt,
            cet_txt,
            p.observacao,
            p.status,
            p.protocolo,
            p.justificativa
        ]

        for col_num, value in enumerate(row, 1):
            cell = ws.cell(row=row_num, column=col_num, value=value)
            cell.border = thin_border
            cell.alignment = Alignment(vertical="center", wrap_text=False)
        
        row_num += 1

    # Ajuste de largura
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        ws.column_dimensions[column].width = (max_length + 2)

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        download_name="relatorio_completo.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --- ROTA DE ATUALIZAÇÃO ---
@bp.route('/admin/atualizar/<int:id>', methods=['POST'])
def atualizar(id):
    if session.get('user_tipo') != 'admin':
        return redirect(url_for('main.login'))
    
    pedido = Solicitacao.query.get_or_404(id)
    
    # Atualiza Geo
    pedido.latitude = request.form.get('latitude')
    pedido.longitude = request.form.get('longitude')
    
    # Atualiza Status Admin
    pedido.protocolo = request.form.get('protocolo')
    pedido.status = request.form.get('status')
    pedido.justificativa = request.form.get('justificativa')
    
    db.session.commit()
    flash('Pedido atualizado com sucesso!', 'success')
    
    return redirect(url_for('main.admin_dashboard'))

# --- NOVO PEDIDO ---
@bp.route('/novo_cadastro', methods=['GET', 'POST'], endpoint='novo')
def novo():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    from datetime import date
    hoje = date.today().isoformat() 

    if request.method == 'POST':
        try:
            user_id_int = int(session['user_id'])

            # Conversão de Data e Hora
            data_obj = datetime.strptime(request.form.get('data'), '%Y-%m-%d').date()
            hora_obj = datetime.strptime(request.form.get('hora'), '%H:%M').time()

            # Conversão de Sim/Não para Booleano (True/False)
            # Se o valor vindo do formulário for 'sim', vira True. Caso contrário, False.
            criadouro_bool = request.form.get('criadouro') == 'sim'
            apoio_cet_bool = request.form.get('apoio_cet') == 'sim'

            nova_solicitacao = Solicitacao(
                data_agendamento=data_obj,
                hora_agendamento=hora_obj,
                foco=request.form.get('foco'),
                
                # Novos Campos
                tipo_visita=request.form.get('tipo_visita'),
                altura_voo=request.form.get('altura_voo'),
                criadouro=criadouro_bool,
                apoio_cet=apoio_cet_bool,
                observacao=request.form.get('observacao'),

                # Endereço e Geo
                cep=request.form.get('cep'),
                logradouro=request.form.get('logradouro'),
                bairro=request.form.get('bairro'),
                cidade=request.form.get('cidade'),
                numero=request.form.get('numero'),
                uf=request.form.get('uf'),
                complemento=request.form.get('complemento'),
                latitude=request.form.get('latitude'),
                longitude=request.form.get('longitude'),

                usuario_id=user_id_int,
                status='PENDENTE'
            )

            db.session.add(nova_solicitacao)
            db.session.commit()

            flash('Pedido enviado com sucesso!', 'success')
            return redirect(url_for('main.dashboard'))

        except ValueError as ve:
             flash(f"Erro no formato de data/hora: {ve}", "warning")
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar: {e}", "danger")

    return render_template('cadastro.html', hoje=hoje)

# --- LOGIN ---
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        if session.get('user_tipo') == 'admin':
            return redirect(url_for('main.admin_dashboard'))
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        user = Usuario.query.filter_by(login=request.form.get('login')).first()

        if user and user.check_senha(request.form.get('senha')):
            session['user_id'] = int(user.id)
            session['user_nome'] = user.nome_uvis
            session['user_tipo'] = user.tipo_usuario

            flash(f'Bem-vindo, {user.nome_uvis}! Login realizado com sucesso.', 'success')
            
            if user.tipo_usuario == 'admin':
                return redirect(url_for('main.admin_dashboard'))
            return redirect(url_for('main.dashboard'))
        else:
            flash('Login ou senha incorretos. Tente novamente.', 'danger')

    return render_template('login.html')

# --- Relatorios ---
@bp.route('/relatorios')
def relatorios():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    # Se não for admin, redireciona
    if session.get('user_tipo') != 'admin':
        flash('Acesso restrito aos administradores.', 'danger')
        return redirect(url_for('main.dashboard'))

    # ---------- 1. Coleta e Filtro de Parâmetros da URL ----------
    
    # Obtém mês e ano da URL (ex: /relatorios?mes=12&ano=2024)
    # Se não houver, usa o mês e ano atuais
    mes_atual = int(request.args.get('mes', datetime.now().month))
    ano_atual = int(request.args.get('ano', datetime.now().year))
    
    # Cria uma base de consulta (query)
    query_base = Solicitacao.query
    
    # Cria os filtros de data (compatível com SQLite)
    filtro_data = f'{ano_atual}-{mes_atual:02d}' 
    
    # Aplica o filtro à consulta base para os totais
    query_filtrada = query_base.filter(
        db.func.strftime('%Y-%m', Solicitacao.data_criacao) == filtro_data
    )
    
    # ---------- 2. Coleta de dados com Filtro e Conversão ----------
    
    total_solicitacoes = query_filtrada.count()
    total_aprovadas = query_filtrada.filter_by(status='APROVADO').count()
    total_recusadas = query_filtrada.filter_by(status='NEGADO').count()
    total_analise = query_filtrada.filter_by(status='EM ANÁLISE').count()

    # Por região (join explícito para evitar ambiguidade) - FILTRADO!
    dados_regiao_raw = (
        db.session.query(Usuario.regiao, db.func.count(Solicitacao.id))
        .join(Usuario, Usuario.id == Solicitacao.usuario_id)
        .filter(db.func.strftime('%Y-%m', Solicitacao.data_criacao) == filtro_data)
        .group_by(Usuario.regiao)
        .all()
    )
    # 💡 CORREÇÃO: Converte objetos Row em tuplas para serialização JSON
    dados_regiao = [tuple(row) for row in dados_regiao_raw]


    # Solicitações por mês (gráfico) — SEM FILTRO de mês/ano, retorna todos os meses para o gráfico
    dados_mensais_raw = (
        db.session.query(
            db.func.strftime('%Y-%m', Solicitacao.data_criacao).label('mes'),
            db.func.count(Solicitacao.id)
        )
        .group_by('mes')
        .order_by('mes')
        .all()
    )
    # 💡 CORREÇÃO: Converte objetos Row em tuplas para serialização JSON
    dados_mensais = [tuple(row) for row in dados_mensais_raw]

    
    # Cria lista de anos disponíveis (usa dados_mensais_raw para extrair os anos únicos)
    anos_disponiveis = sorted(list(set([d[0].split('-')[0] for d in dados_mensais])), reverse=True)
    
    # ---------- 3. Renderização ----------
    return render_template(
        'relatorios.html',
        total_solicitacoes=total_solicitacoes,
        total_aprovadas=total_aprovadas,
        total_recusadas=total_recusadas,
        total_analise=total_analise,
        dados_regiao=dados_regiao,
        dados_mensais=dados_mensais,
        
        # Envia os filtros ativos para o HTML
        mes_selecionado=mes_atual,
        ano_selecionado=ano_atual,
        anos_disponiveis=anos_disponiveis
    )

# --- LOGOUT ---
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

@bp.route("/forcar_erro")
def forcar_erro():
    1 / 0  # erro proposital
    return "nunca vai chegar aqui"