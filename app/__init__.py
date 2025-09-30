from flask import Flask
from config import Config
# 1. Importe 'api' do seu arquivo de extensões
from .extensions import db, jwt, cors, api
from .models import Usuario # Mantenha a importação de um modelo para garantir o contexto do DB

def create_app(config_class=Config):
    '''
    Fábrica de Aplicação: Cria e configura a instância do Flask.
    '''
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicialize todas as extensões com a aplicação
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)  
    api.init_app(app)

    # Registar os seus Namespaces (que virão dos arquivos de rotas)
    # Lembra de criar e importar as variáveis 'auth_ns' e 'pokemon_ns'
    # dos seus respectivos arquivos routes.py
    from .auth.routes import auth_ns # Alias temporário se ainda não renomeou
    api.add_namespace(auth_ns, path='/api/auth')

    from .pokemon.routes import pokemon_ns # Alias temporário se ainda não renomeou
    api.add_namespace(pokemon_ns, path='/api/pokemon')

    # Criar as tabelas do banco de dados, se não existirem
    with app.app_context():
        db.create_all()

    return app