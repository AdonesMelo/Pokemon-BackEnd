from flask import request
from flask_restx import Namespace, Resource, fields
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from app.models import Usuario
from app.extensions import db

# Criar o Namespace
auth_ns = Namespace('auth', description='Operações de Autenticação e Gerenciamento de Usuários')

# Definir os Modelos de Dados
modelo_registro = auth_ns.model('Registro', {
    'nome': fields.String(required=True, description='Nome do usuário'),
    'email': fields.String(required=True, description='Email para login'),
    'senha': fields.String(required=True, description='Senha de acesso'),
})

modelo_login = auth_ns.model('Login', {
    'email': fields.String(required=True, description='Email do usuário'),
    'senha': fields.String(required=True, description='Senha do usuário'),
})

modelo_token = auth_ns.model('Token', {
    'token': fields.String(description='Token de acesso JWT')
})

modelo_perfil = auth_ns.model('Perfil', {
    'id': fields.Integer(description='ID do usuário'),
    'nome': fields.String(description='Nome do usuário'),
    'email': fields.String(description='Email do usuário'),
})

modelo_mensagem = auth_ns.model('Mensagem', {
    'mensagem': fields.String
})


# Definir os Recursos (Resources)
@auth_ns.route('/register')
class Registro(Resource):
    @auth_ns.expect(modelo_registro, validate=True)
    @auth_ns.response(201, 'Usuário cadastrado com sucesso', modelo_mensagem)
    @auth_ns.response(400, 'Email já cadastrado')
    def post(self):
        '''Cria um novo usuário'''
        data = request.get_json()
        
        if Usuario.query.filter_by(email=data['email']).first():
            return {'mensagem': 'Email já cadastrado'}, 400

        senha_hash = generate_password_hash(data['senha'])
        novo_usuario = Usuario(nome=data['nome'], email=data['email'], senha=senha_hash)
        
        db.session.add(novo_usuario)
        db.session.commit()

        return {'mensagem': 'Usuário cadastrado com sucesso'}, 201

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(modelo_login, validate=True)
    @auth_ns.marshal_with(modelo_token, code=200, description='Login bem-sucedido')
    @auth_ns.response(401, 'Credenciais inválidas')
    def post(self):
        '''Autentica um usuário e retorna um token JWT'''
        data = request.get_json()
        usuario = Usuario.query.filter_by(email=data.get('email')).first()
        
        # Lógica completa para verificar a senha e retornar o token
        if not usuario or not check_password_hash(usuario.senha, data.get('senha')):
            auth_ns.abort(401, 'Credenciais inválidas')

        token = create_access_token(identity=str(usuario.id))
        return {'token': token}

@auth_ns.route('/perfil')
class Perfil(Resource):
    # Protege o endpoint com JWT
    method_decorators = [jwt_required()]

    @auth_ns.marshal_with(modelo_perfil)
    @auth_ns.doc(security='jsonWebToken') # Informa ao Swagger que esta rota precisa de autorização
    @auth_ns.response(404, 'Usuário não encontrado')
    def get(self):
        '''Obtém as informações do perfil do usuário logado'''
        usuario_id = get_jwt_identity()
        usuario = db.session.get(Usuario, usuario_id)
        
        if not usuario:
            auth_ns.abort(404, 'Usuário não encontrado')
            
        return usuario