import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'sua-chave-secreta-para-desenvolvimento')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'sua-chave-jwt-para-desenvolvimento')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///pokemon.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SWAGGER = {
        'title': 'API de Pokémon',
        'uiversion': 3,
        'swagger_ui': True,        # Garante que a UI está habilitada
        'specs_route': '/swagger/' # <-- MUDANÇA IMPORTANTE: Nova URL
    }