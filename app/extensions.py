from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_restx import Api

autorizacoes = {
    'jsonWebToken': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': "Digite 'Bearer ' antes do seu token JWT. Ex: 'Bearer [token]'"
    }
}

api = Api(
    title='API de Pokémon',
    version='1.0',
    description='Uma API para gerenciar grupos de batalha Pokémon',
    authorizations=autorizacoes
)

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()