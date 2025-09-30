from datetime import datetime
from .extensions import db

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

class TipoPokemon(db.Model):
    __tablename__ = 'tipos_pokemon'
    id = db.Column(db.Integer, primary_key=True)
    nome_tipo = db.Column(db.String(50), nullable=False, unique=True)
    cor = db.Column(db.String(20))

class Pokemon(db.Model):
    __tablename__ = 'pokemons'
    # Campos existentes
    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    nome_pokemon = db.Column(db.String(100), nullable=False, unique=True)
    url_imagem = db.Column(db.String(255))
    altura = db.Column(db.Float)
    peso = db.Column(db.Float)
    tipo_id = db.Column(db.Integer, db.ForeignKey('tipos_pokemon.id'))

    # --- NOVOS CAMPOS PARA ATRIBUTOS ---
    hp = db.Column(db.Integer, default=0)
    attack = db.Column(db.Integer, default=0)
    defense = db.Column(db.Integer, default=0)
    special_attack = db.Column(db.Integer, default=0)
    special_defense = db.Column(db.Integer, default=0)
    speed = db.Column(db.Integer, default=0)

class PokemonUsuario(db.Model):
    __tablename__ = 'pokemons_usuario'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    pokemon_id = db.Column(db.Integer, db.ForeignKey('pokemons.id'))
    favorito = db.Column(db.Boolean, default=False)
    grupo_batalha = db.Column(db.Boolean, default=False)

