from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import json
import os
import socket
from flask_cors import CORS
import jwt
from datetime import datetime, timedelta

# Configurações para Smart TVs
ALLOWED_IPS = ['127.0.0.1', 'localhost']  # IPs permitidos
SMART_TV_IPS = []  # Lista para armazenar IPs de Smart TVs

app = Flask(__name__, static_folder='public')
app.config['SECRET_KEY'] = os.urandom(24)  # Chave secreta para segurança

# Configurar CORS para permitir conexões locais e Smart TVs
CORS(app, resources={
    r"/*": {
        "origins": ["https://osmarads.onrender.com", "http://localhost:3000", "https://osmarads.onrender.com:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "supports_credentials": True
    }
})

# Configurar Socket.IO com suporte a Smart TVs e configurações de produção
socketio = SocketIO(
    app,
    cors_allowed_origins=["https://osmarads.onrender.com", "http://localhost:3000", "https://osmarads.onrender.com:3000"],
    ping_timeout=60,
    ping_interval=25,
    async_mode='eventlet',
    logger=True,
    engineio_logger=True,
    cors_credentials=True,
    allow_upgrades=True,
    http_compression=True,
    cookie=None,
    async_handlers=True,
    always_connect=True,
    transports=['websocket', 'polling']
)

# Função para verificar IP
def is_allowed_ip(ip):
    return ip in ALLOWED_IPS or ip in SMART_TV_IPS

# Função para verificar se é uma Smart TV
def is_smart_tv(request):
    user_agent = request.headers.get('User-Agent', '')
    return 'LG' in user_agent or 'webOS' in user_agent

# Função para registrar Smart TV
@app.route('/api/smart-tv/register', methods=['POST'])
def register_smart_tv():
    ip = request.remote_addr
    if is_smart_tv(request):
        SMART_TV_IPS.append(ip)
        return jsonify({'message': 'Smart TV registrada com sucesso'}), 200
    return jsonify({'error': 'Dispositivo não é uma Smart TV'}), 400
USERS_FILE = os.path.join(os.path.dirname(__file__), 'usuarios.json')

# Utilitários para ler/salvar usuários
def read_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    users = read_users()
    if any(u['email'] == data['email'] for u in users):
        return jsonify({'error': 'Email já cadastrado'}), 400
    senha = data.get('password') or data.get('senha')
    user = {
        'nome': data['nome'],
        'email': data['email'],
        'senha': senha,
        'tipo': 'cliente'
    }
    users.append(user)
    save_users(users)
    return jsonify({'message': 'Usuário cadastrado com sucesso!'}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.json
        
        # Validação de dados
        if not data or 'email' not in data or ('password' not in data and 'senha' not in data):
            return jsonify({
                'error': 'Dados de login inválidos',
                'details': 'Email e senha são obrigatórios'
            }), 400
            
        # Obter senha
        senha = data.get('password') or data.get('senha')
        if not senha:
            return jsonify({
                'error': 'Senha inválida',
                'details': 'Senha não fornecida'
            }), 400
            
        # Carregar usuários
        users = read_users()
        if not users:
            return jsonify({
                'error': 'Erro de sistema',
                'details': 'Nenhum usuário cadastrado'
            }), 500
            
        # Verificar credenciais
        user = next((u for u in users if u['email'] == data['email']), None)
        if not user or user['senha'] != senha:
            return jsonify({
                'error': 'Credenciais inválidas',
                'details': 'Email ou senha incorretos'
            }), 401
        
        # Gerar token JWT
        try:
            token = jwt.encode(
                {
                    'email': user['email'],
                    'exp': datetime.utcnow() + timedelta(hours=1)
                },
                app.config['SECRET_KEY']
            )
        except Exception as e:
            print(f'Erro ao gerar token: {str(e)}')
            return jsonify({
                'error': 'Erro de autenticação',
                'details': 'Falha ao gerar token de acesso'
            }), 500
            
        # Resposta
        response = {
            'message': 'Login realizado com sucesso',
            'user': {
                'email': user['email'],
                'nome': user['nome'],
                'tipo': user['tipo']
            },
            'token': token
        }
        
        # Para Smart TVs, retornar token no localStorage
        if is_smart_tv(request):
            response['localStorage'] = True
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f'Erro no login: {str(e)}')
        return jsonify({
            'error': 'Erro interno do servidor',
            'details': str(e)
        }), 500

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# Configurar diretório de uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Rota para servir arquivos de upload
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    try:
        # Verificar se o arquivo existe de forma segura
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.isfile(filepath):
            return jsonify({"error": "Arquivo não encontrado"}), 404
        
        # Determinar o tipo MIME com base na extensão
        mimetype = 'application/octet-stream'
        ext = filename.lower().split('.')[-1]
        
        if ext in ['png', 'jpg', 'jpeg', 'gif']:
            mimetype = f'image/{ext}'
        elif ext in ['mp4']:
            mimetype = 'video/mp4'
        elif ext in ['webm']:
            mimetype = 'video/webm'
        elif ext in ['ogg']:
            mimetype = 'video/ogg'
        
        # Configurar cabeçalhos CORS
        response = send_from_directory(
            app.config['UPLOAD_FOLDER'],
            filename,
            mimetype=mimetype,
            as_attachment=False,
            conditional=True
        )
        
        # Adicionar cabeçalhos de cache e CORS
        response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 ano
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response
        
    except Exception as e:
        app.logger.error(f"Erro ao servir arquivo {filename}: {str(e)}")
        return jsonify({"error": "Erro ao processar o arquivo"}), 500

# Rota para servir qualquer arquivo da pasta public
@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('public', filename)

# Utilitários para ler/salvar outdoors
OUTDOORS_FILE = os.path.join(os.path.dirname(__file__), 'outdoors.json')
def read_outdoors():
    if not os.path.exists(OUTDOORS_FILE):
        return []
    with open(OUTDOORS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)
def save_outdoors(outdoors):
    with open(OUTDOORS_FILE, 'w', encoding='utf-8') as f:
        json.dump(outdoors, f, ensure_ascii=False, indent=2)

# Rota para criar outdoor
@app.route('/api/outdoors', methods=['POST'])
def create_outdoor():
    data = request.json
    nome = data.get('nome')
    localizacao = data.get('localizacao')
    tipo = data.get('tipo')
    usuario = data.get('usuario')
    tipos_validos = ['LED', 'LCD', 'projetor']
    if not nome or not localizacao or not tipo or not usuario:
        return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
    if tipo.upper() not in ['LED', 'LCD'] and tipo.lower() != 'projetor':
        return jsonify({'error': 'Tipo deve ser LED, LCD ou projetor'}), 400
    # Normaliza tipo para manter padrão
    if tipo.lower() == 'projetor':
        tipo_final = 'projetor'
    else:
        tipo_final = tipo.upper()
    outdoors = read_outdoors()
    new_id = (max([o['id'] for o in outdoors], default=0) + 1) if outdoors else 1
    outdoor = {
        'id': new_id,
        'nome': nome,
        'localizacao': localizacao,
        'tipo': tipo_final,
        'usuario': usuario
    }
    outdoors.append(outdoor)
    save_outdoors(outdoors)
    return jsonify({'message': 'Outdoor criado com sucesso!', 'outdoor': outdoor}), 201

# Rota para listar todos os outdoors
@app.route('/api/outdoors', methods=['GET'])
def list_outdoors():
    outdoors = read_outdoors()
    return jsonify(outdoors)

# Rota para obter, editar e deletar outdoor por id
@app.route('/api/outdoors/<int:id>', methods=['GET'])
def get_outdoor(id):
    outdoors = read_outdoors()
    outdoor = next((o for o in outdoors if o['id'] == id), None)
    if not outdoor:
        return jsonify({'error': 'Outdoor não encontrado'}), 404
    return jsonify(outdoor)

@app.route('/api/outdoors/<int:id>', methods=['PUT'])
def update_outdoor(id):
    data = request.json
    outdoors = read_outdoors()
    idx = next((i for i, o in enumerate(outdoors) if o['id'] == id), None)
    if idx is None:
        return jsonify({'error': 'Outdoor não encontrado'}), 404
    # Atualiza apenas os campos permitidos
    for campo in ['nome', 'localizacao', 'tipo', 'usuario']:
        if campo in data:
            outdoors[idx][campo] = data[campo]
    save_outdoors(outdoors)
    return jsonify({'message': 'Outdoor atualizado com sucesso!', 'outdoor': outdoors[idx]})

@app.route('/api/outdoors/<int:id>', methods=['DELETE'])
def delete_outdoor(id):
    outdoors = read_outdoors()
    new_outdoors = [o for o in outdoors if o['id'] != id]
    if len(new_outdoors) == len(outdoors):
        return jsonify({'error': 'Outdoor não encontrado'}), 404
    save_outdoors(new_outdoors)
    return jsonify({'message': 'Outdoor excluído com sucesso!'})

# Rota para listar outdoors do usuário
@app.route('/api/outdoors/meus', methods=['GET'])
def list_outdoors_meus():
    usuario = request.args.get('usuario')
    if not usuario:
        return jsonify({'error': 'Usuário não informado'}), 400
    outdoors = read_outdoors()
    meus = [o for o in outdoors if o.get('usuario') == usuario]
    return jsonify(meus)

# Vincular anúncio a outdoor
@app.route('/api/outdoors/<int:outdoor_id>/anuncios/<anuncio_id>', methods=['POST'])
def vincular_anuncio(outdoor_id, anuncio_id):
    try:
        outdoors = read_outdoors()
        anuncios = read_anuncios()
        outdoor = next((o for o in outdoors if o['id'] == outdoor_id), None)
        anuncio = next((a for a in anuncios if a['_id'] == anuncio_id), None)
        
        if not outdoor or not anuncio:
            return jsonify({'error': 'Outdoor ou anúncio não encontrado'}), 404
            
        # Verificar se o outdoor pertence ao mesmo usuário do anúncio
        if outdoor.get('usuario') != anuncio.get('usuario'):
            return jsonify({'error': 'O anúncio não pertence ao mesmo usuário do outdoor'}), 403
            
        if 'anuncios' not in outdoor:
            outdoor['anuncios'] = []
            
        if anuncio_id not in outdoor['anuncios']:
            outdoor['anuncios'].append(anuncio_id)
            save_outdoors(outdoors)
            # Notificar players sobre a atualização
            socketio.start_background_task(notify_outdoor_update, outdoor_id)
            
        return jsonify({'message': 'Anúncio vinculado com sucesso!'}), 200
        
    except Exception as e:
        print('Erro ao vincular anúncio:', str(e))
        return jsonify({'error': 'Erro ao vincular anúncio'}), 500

# Listar anúncios vinculados a um outdoor
@app.route('/api/outdoors/<int:outdoor_id>/anuncios', methods=['GET'])
def get_anuncios_vinculados(outdoor_id):
    try:
        outdoors = read_outdoors()
        anuncios = read_anuncios()
        outdoor = next((o for o in outdoors if o['id'] == outdoor_id), None)
        if not outdoor:
            return jsonify({'error': 'Outdoor não encontrado'}), 404
        
        if 'anuncios' not in outdoor or not outdoor['anuncios']:
            return jsonify([])
        
        # Retorna os anúncios na ordem definida em outdoor['anuncios']
        vinculados_ordenados = []
        for aid in outdoor['anuncios']:
            anuncio = next((a for a in anuncios if a['_id'] == aid), None)
            if anuncio:
                # Se houver sobrescrita local, aplicar as alterações
                if 'anuncios_vinculados' in outdoor and aid in outdoor['anuncios_vinculados']:
                    anuncio_atualizado = anuncio.copy()
                    anuncio_atualizado.update(outdoor['anuncios_vinculados'][aid])
                    vinculados_ordenados.append(anuncio_atualizado)
                else:
                    vinculados_ordenados.append(anuncio)
        
        return jsonify(vinculados_ordenados)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/outdoors/<int:outdoor_id>/anuncios/<anuncio_id>/vinculado', methods=['PATCH'])
def patch_anuncio_vinculado(outdoor_id, anuncio_id):
    data = request.json
    outdoors = read_outdoors()
    anuncios = read_anuncios()
    outdoor = next((o for o in outdoors if o['id'] == outdoor_id), None)
    if not outdoor:
        return jsonify({'error': 'Outdoor não encontrado'}), 404
    if 'anuncios' not in outdoor or anuncio_id not in outdoor['anuncios']:
        return jsonify({'error': 'Anúncio não vinculado a este outdoor'}), 404
    # Busca se já existe sobrescrita local
    if 'anuncios_vinculados' not in outdoor:
        outdoor['anuncios_vinculados'] = {}
    if anuncio_id not in outdoor['anuncios_vinculados']:
        # Inicializa sobrescrita local a partir do global
        anuncio_global = next((a for a in anuncios if a['_id'] == anuncio_id), None)
        if not anuncio_global:
            return jsonify({'error': 'Anúncio não encontrado'}), 404
        outdoor['anuncios_vinculados'][anuncio_id] = {
            'titulo': anuncio_global['titulo'],
            'duracao': anuncio_global['duracao']
        }
    # Atualiza apenas título e duração
    if 'titulo' in data:
        outdoor['anuncios_vinculados'][anuncio_id]['titulo'] = data['titulo']
    if 'duracao' in data:
        outdoor['anuncios_vinculados'][anuncio_id]['duracao'] = data['duracao']
    save_outdoors(outdoors)
    return jsonify({'message': 'Anúncio vinculado atualizado com sucesso!', 'anuncio': outdoor['anuncios_vinculados'][anuncio_id]})

    outdoors = read_outdoors()
    anuncios = read_anuncios()
    outdoor = next((o for o in outdoors if o['id'] == outdoor_id), None)
    if not outdoor:
        return jsonify({'error': 'Outdoor não encontrado'}), 404
    if 'anuncios' not in outdoor or not outdoor['anuncios']:
        return jsonify([])
    # Retorna os anúncios na ordem definida em outdoor['anuncios']
    anuncios_dict = {a['_id']: a for a in anuncios}
    vinculados_ordenados = [anuncios_dict[aid] for aid in outdoor['anuncios'] if aid in anuncios_dict]
    return jsonify(vinculados_ordenados)

# Desvincular anúncio de outdoor
@app.route('/api/outdoors/<int:outdoor_id>/anuncios/<anuncio_id>', methods=['DELETE'])
def desvincular_anuncio(outdoor_id, anuncio_id):
    try:
        outdoors = read_outdoors()
        outdoor = next((o for o in outdoors if o['id'] == outdoor_id), None)
        if not outdoor or 'anuncios' not in outdoor or anuncio_id not in outdoor['anuncios']:
            return jsonify({'error': 'Vínculo não encontrado'}), 404
        
        # Remover o anúncio da lista
        outdoor['anuncios'].remove(anuncio_id)
        
        # Se houver anúncios vinculados, remover também
        if 'anuncios_vinculados' in outdoor and anuncio_id in outdoor['anuncios_vinculados']:
            del outdoor['anuncios_vinculados'][anuncio_id]
        
        save_outdoors(outdoors)
        
        # Notificar players sobre a atualização
        socketio.start_background_task(notify_outdoor_update, outdoor_id)
        
        return jsonify({'message': 'Anúncio desvinculado com sucesso'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---- ANUNCIOS ----
import uuid
from werkzeug.utils import secure_filename
ANUNCIOS_FILE = os.path.join(os.path.dirname(__file__), 'anuncios.json')
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def read_anuncios():
    if not os.path.exists(ANUNCIOS_FILE):
        return []
    with open(ANUNCIOS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_anuncios(anuncios):
    with open(ANUNCIOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(anuncios, f, ensure_ascii=False, indent=2)

# Rota para criar anúncio com upload
@app.route('/api/anuncios', methods=['POST'])
def create_anuncio():
    try:
        # Obter o token do cabeçalho de autorização
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token de autenticação não fornecido'}), 401
            
        token = auth_header.split(' ')[1]
        
        try:
            # Decodificar o token para obter o email do usuário
            decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user_email = decoded['email']
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
            return jsonify({'error': 'Token inválido ou expirado'}), 401
        
        data = request.form
        
        # Verificar se o usuário existe
        users = read_users()
        user = next((u for u in users if u['email'] == user_email), None)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
            
        titulo = data.get('titulo')
        tipo = data.get('tipo')
        duracao = data.get('duracao')
        arquivo = None
        
        if 'arquivo' in request.files:
            arquivo_obj = request.files['arquivo']
            # Gera nome seguro e único
            filename = f"{uuid.uuid4()}_{secure_filename(arquivo_obj.filename)}"
            caminho = os.path.join(UPLOAD_FOLDER, filename)
            arquivo_obj.save(caminho)
            arquivo = filename
            
        anuncio = {
            '_id': str(uuid.uuid4()),
            'titulo': titulo,
            'tipo': tipo,
            'duracao': duracao,
            'arquivo': arquivo,
            'usuario': user_email,  # Usando o email do token JWT
            'data_criacao': datetime.now().isoformat()
        }
        
        anuncios = read_anuncios()
        anuncios.append(anuncio)
        save_anuncios(anuncios)
        
        return jsonify({'message': 'Anúncio criado com sucesso!', 'anuncio': anuncio}), 201
        
    except Exception as e:
        print('Erro ao criar anúncio:', str(e))
        return jsonify({'error': 'Erro ao criar anúncio'}), 500

@app.route('/api/anuncios/meus', methods=['GET'])
def get_anuncios_meus():
    # Obter o token do cabeçalho de autorização
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token de autenticação não fornecido'}), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        # Decodificar o token para obter o email do usuário
        decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_email = decoded['email']
        
        # Filtrar anúncios pelo email do usuário
        anuncios = read_anuncios()
        anuncios_usuario = [a for a in anuncios if a.get('usuario') == user_email]
        
        return jsonify(anuncios_usuario)
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token inválido'}), 401

@app.route('/api/anuncios/<id>', methods=['PATCH'])
def patch_anuncio(id):
    # Verificar autenticação
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token de autenticação não fornecido'}), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        # Decodificar o token para obter o email do usuário
        decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_email = decoded['email']
        
        anuncios = read_anuncios()
        anuncio_index = next((i for i, a in enumerate(anuncios) if a['_id'] == id), None)
        
        if anuncio_index is None:
            return jsonify({'error': 'Anúncio não encontrado'}), 404
            
        # Verificar se o usuário é o dono do anúncio
        if anuncios[anuncio_index].get('usuario') != user_email:
            return jsonify({'error': 'Você não tem permissão para editar este anúncio'}), 403
            
        # Obter outdoor_id antes de atualizar
        outdoor_id = anuncios[anuncio_index].get('outdoor_id')
        
        # Atualizar apenas os campos fornecidos
        data = request.get_json()
        for key, value in data.items():
            if key != '_id' and key != 'id':  # Não permitir alterar o ID
                anuncios[anuncio_index][key] = value
        
        # Atualizar data de modificação
        anuncios[anuncio_index]['ultima_atualizacao'] = datetime.now().isoformat()
                
        save_anuncios(anuncios)
        
        # Notificar atualização do anúncio
        if outdoor_id:
            notify_anuncio_update(outdoor_id, id)
        
        return jsonify(anuncios[anuncio_index])
        
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token inválido'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/anuncios/<id>', methods=['DELETE'])
def delete_anuncio(id):
    # Verificar autenticação
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token de autenticação não fornecido'}), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        # Decodificar o token para obter o email do usuário
        decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_email = decoded['email']
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
        return jsonify({'error': 'Token inválido ou expirado'}), 401
    
    anuncios = read_anuncios()
    anuncio = next((a for a in anuncios if a['_id'] == id), None)
    
    if not anuncio:
        return jsonify({'error': 'Anúncio não encontrado'}), 404
    
    # Verificar se o usuário é o dono do anúncio
    if anuncio.get('usuario') != user_email:
        return jsonify({'error': 'Você não tem permissão para excluir este anúncio'}), 403
    
    # Excluir arquivo do disco, se existir
    if anuncio.get('arquivo'):
        caminho = os.path.join(UPLOAD_FOLDER, anuncio['arquivo'])
        if os.path.exists(caminho):
            try:
                os.remove(caminho)
            except Exception as e:
                print(f'Erro ao excluir arquivo: {e}')
    
    # Remove do json
    anuncios = [a for a in anuncios if a['_id'] != id]
    save_anuncios(anuncios)
    return jsonify({'message': 'Anúncio excluído com sucesso!'})

@app.route('/api/outdoors/<int:outdoor_id>/anuncios/ordem', methods=['PATCH'])
def atualizar_ordem_anuncios(outdoor_id):
    try:
        data = request.json
        if 'anuncios' not in data or not isinstance(data['anuncios'], list):
            return jsonify({'error': 'Lista de anúncios inválida'}), 400
        
        outdoors = read_outdoors()
        outdoor = next((o for o in outdoors if o['id'] == outdoor_id), None)
        if not outdoor:
            return jsonify({'error': 'Outdoor não encontrado'}), 404
        
        # Verificar se todos os IDs fornecidos existem no outdoor
        anuncios_validos = all(anuncio_id in (outdoor.get('anuncios') or []) for anuncio_id in data['anuncios'])
        if not anuncios_validos:
            return jsonify({'error': 'Um ou mais IDs de anúncio não pertencem a este outdoor'}), 400
        
        # Atualizar a ordem dos anúncios
        outdoor['anuncios'] = data['anuncios']
        save_outdoors(outdoors)
        
        # Notificar os players sobre a mudança
        socketio.start_background_task(notify_outdoor_update, outdoor_id)
        
        return jsonify({
            'message': 'Ordem dos anúncios atualizada com sucesso',
            'anuncios': data['anuncios']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/outdoors/<int:outdoor_id>/anuncios/ordem', methods=['PUT'])
def atualizar_ordem_anuncios_put(outdoor_id):
    try:
        data = request.json
        nova_ordem = data.get('ordem')
        if not isinstance(nova_ordem, list):
            return jsonify({'error': 'Ordem inválida'}), 400
            
        outdoors = read_outdoors()
        outdoor = next((o for o in outdoors if o['id'] == outdoor_id), None)
        if not outdoor:
            return jsonify({'error': 'Outdoor não encontrado'}), 404
            
        # Verificar se todos os IDs fornecidos existem no outdoor
        anuncios_validos = all(anuncio_id in (outdoor.get('anuncios') or []) for anuncio_id in nova_ordem)
        if not anuncios_validos:
            return jsonify({'error': 'Um ou mais IDs de anúncio não pertencem a este outdoor'}), 400
            
        # Atualizar a ordem dos anúncios
        outdoor['anuncios'] = nova_ordem
        save_outdoors(outdoors)
        
        # Notificar os players sobre a mudança
        socketio.start_background_task(notify_outdoor_update, outdoor_id)
        
        return jsonify({
            'message': 'Ordem dos anúncios atualizada com sucesso',
            'anuncios': nova_ordem
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    print('Cliente conectado')

@socketio.on('disconnect')
def handle_disconnect():
    print('Cliente desconectado')

@socketio.on('join_outdoor')
def handle_join_outdoor(data):
    """Adiciona o cliente à sala do outdoor para receber atualizações"""
    outdoor_id = data.get('outdoor_id')
    if outdoor_id:
        from flask_socketio import join_room
        join_room(outdoor_id)
        print(f'Cliente entrou na sala do outdoor {outdoor_id}')

# Função para notificar players sobre mudanças em um outdoor
def notify_outdoor_update(outdoor_id):
    """Notifica todos os players conectados ao outdoor sobre uma atualização"""
    print(f"Notificando atualização do outdoor {outdoor_id}")
    socketio.emit('outdoor_updated', {'outdoor_id': str(outdoor_id)}, room=str(outdoor_id))

# Função para notificar players sobre atualização de um anúncio
def notify_anuncio_update(outdoor_id, anuncio_id):
    """Notifica sobre a atualização de um anúncio específico"""
    print(f"Notificando atualização do anúncio {anuncio_id} no outdoor {outdoor_id}")
    socketio.emit('anuncio_updated', {
        'outdoor_id': str(outdoor_id),
        'anuncio_id': str(anuncio_id)
    }, room=str(outdoor_id))



if __name__ == '__main__':
    @app.route('/api/outdoor/<outdoor_id>/player/reload', methods=['POST'])
    def reload_player(outdoor_id):
        # Verificar se é uma Smart TV
        if is_smart_tv(request):
            # Para Smart TVs, enviar mensagem específica
            socketio.emit('reloadPlayer', {
                'outdoor_id': outdoor_id,
                'device_type': 'smart-tv'
        }, broadcast=True)
        else:
            socketio.emit('reloadPlayer', {'outdoor_id': outdoor_id})
        
        return jsonify({'message': 'Comando de recarregamento enviado'}), 200

    socketio.run(app, host='0.0.0.0', port=3000, debug=True)