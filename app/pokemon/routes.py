
import requests
from flask import request
from flask_restx import Namespace, Resource, fields, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import Pokemon, TipoPokemon, PokemonUsuario
from app.extensions import db

# --- Namespace e Modelos ---
pokemon_ns = Namespace('pokemon', description='Operações relacionadas a Pokémon e grupos de batalha')

# Modelo para a maioria das respostas de Pokémon
modelo_pokemon_simples = pokemon_ns.model('PokemonSimples', {
    'id': fields.Integer(description='ID do Pokémon'),
    'nome': fields.String(description='Nome do Pokémon'),
    'imagem': fields.String(description='URL da imagem do Pokémon'),
    'tipo': fields.String(description='Tipo principal do Pokémon'),
})

# Modelos para Grupo de Batalha
modelo_grupo_entrada = pokemon_ns.model('GrupoEntrada', {
    'grupo': fields.List(fields.Integer, required=True, description='Lista de IDs dos Pokémon para o grupo de batalha (máximo 6)')
})
modelo_grupo_resposta = pokemon_ns.model('GrupoResposta', {
    'grupo': fields.List(fields.Nested(modelo_pokemon_simples), description='Lista de Pokémon no grupo de batalha')
})

# Modelo para Lista de Favoritos
modelo_favoritos_resposta = pokemon_ns.model('FavoritosResposta', {
    'favoritos': fields.List(fields.Nested(modelo_pokemon_simples), description='Lista de Pokémon favoritos')
})

# Modelo para mensagens genéricas
modelo_mensagem = pokemon_ns.model('MensagemSimples', {
    'mensagem': fields.String
})

# --- NOVO MODELO PARA A RESPOSTA DA LISTAGEM ---
modelo_listagem_pokemon = pokemon_ns.model('ListagemPokemon', {
    'items': fields.List(fields.Nested(modelo_pokemon_simples)),
    'total': fields.Integer(description='Total de itens encontrados'),
    'page': fields.Integer(description='Página atual'),
    'pages': fields.Integer(description='Total de páginas'),
    'per_page': fields.Integer(description='Itens por página'),
})

# --- NOVO PARSER PARA OS ARGUMENTOS DE FILTRO E PAGINAÇÃO ---
listagem_parser = reqparse.RequestParser()
listagem_parser.add_argument('page', type=int, default=1, help='Número da página')
listagem_parser.add_argument('per_page', type=int, default=12, help='Itens por página')
listagem_parser.add_argument('nome', type=str, default='', help='Filtrar por nome do Pokémon')


# --- Função Auxiliar ---
def garantir_pokemon_no_db(pokemon_id):
    '''Verifica se um Pokémon existe no DB local. Se não, busca na PokeAPI e o salva.'''
    pokemon = Pokemon.query.get(pokemon_id)
    if pokemon:
        return pokemon

    url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_id}'
    res = requests.get(url)
    if res.status_code != 200:
        return None

    data = res.json()
    nome = data.get('name')
    # Torna a busca pela imagem mais segura, evitando erros se 'sprites' não existir
    imagem = data.get('sprites', {}).get('front_default')
    altura = data.get('height')
    peso = data.get('weight')
    tipos = [t['type']['name'] for t in data.get('types', [])]

    tipo_principal = tipos[0] if tipos else None
    tipo_obj = None
    if tipo_principal:
        tipo_obj = TipoPokemon.query.filter_by(nome_tipo=tipo_principal).first()
        if not tipo_obj:
            tipo_obj = TipoPokemon(nome_tipo=tipo_principal)
            db.session.add(tipo_obj)
            db.session.commit()

    novo_pokemon = Pokemon(
        id=pokemon_id,
        nome_pokemon=nome,
        url_imagem=imagem,
        altura=altura,
        peso=peso,
        tipo_id=tipo_obj.id if tipo_obj else None
    )
    db.session.add(novo_pokemon)
    db.session.commit()
    print(f'Pokémon {nome} (ID: {pokemon_id}) salvo no DB com sucesso.')
    return novo_pokemon

# --- NOVO RECURSO PARA A LISTAGEM DE POKÉMON ---
@pokemon_ns.route('/listagem')
class ListagemPokemon(Resource):
    @pokemon_ns.marshal_with(modelo_listagem_pokemon)
    @pokemon_ns.expect(listagem_parser)
    def get(self):
        '''Lista e filtra os Pokémon da base de dados local com paginação.'''
        args = listagem_parser.parse_args()
        page = args['page']
        per_page = args['per_page']
        nome_filtro = args['nome']

        query = Pokemon.query

        if nome_filtro:
            # .ilike() faz uma pesquisa "case-insensitive"
            query = query.filter(Pokemon.nome_pokemon.ilike(f'%{nome_filtro}%'))
        
        paginacao = query.order_by(Pokemon.id).paginate(page=page, per_page=per_page, error_out=False)
        
        # Formata os itens para corresponder ao modelo de resposta
        items_formatados = []
        for pokemon in paginacao.items:
            tipo = db.session.get(TipoPokemon, pokemon.tipo_id) if pokemon.tipo_id else None
            items_formatados.append({
                'id': pokemon.id,
                'nome': pokemon.nome_pokemon,
                'imagem': pokemon.url_imagem,
                'tipo': tipo.nome_tipo if tipo else 'N/A'
            })
            
        return {
            'items': items_formatados,
            'total': paginacao.total,
            'page': paginacao.page,
            'pages': paginacao.pages,
            'per_page': paginacao.per_page,
        }

@pokemon_ns.route('/busca/<string:nome>')
class BuscaPokemon(Resource):
    @pokemon_ns.doc('busca_pokemon')
    @pokemon_ns.response(404, 'Pokémon não encontrado')
    def get(self, nome):
        '''Busca dados de um Pokémon específico na PokeAPI'''
        url = f'https://pokeapi.co/api/v2/pokemon/{nome.lower()}'
        response = requests.get(url)

        if response.status_code == 200:
            return response.json()
        else:
            pokemon_ns.abort(404, 'Pokémon não encontrado')

@pokemon_ns.route('/<int:pokemon_id>/favoritar')
@pokemon_ns.param('pokemon_id', 'O ID do Pokémon a ser favoritado/desfavoritado')
class FavoritarPokemon(Resource):
    method_decorators = [jwt_required()]

    @pokemon_ns.doc(security='jsonWebToken')
    @pokemon_ns.response(200, 'Pokémon marcado como favorito.', modelo_mensagem)
    def post(self, pokemon_id):
        '''Marca um Pokémon como favorito para o utilizador logado.'''
        usuario_id = get_jwt_identity()
        pokemon = garantir_pokemon_no_db(pokemon_id)
        if not pokemon:
            return {'mensagem': 'Pokémon não encontrado na PokeAPI'}, 404
        
        relacao = PokemonUsuario.query.filter_by(usuario_id=usuario_id, pokemon_id=pokemon.id).first()
        
        if relacao:
            relacao.favorito = True
        else:
            nova_relacao = PokemonUsuario(usuario_id=usuario_id, pokemon_id=pokemon.id, favorito=True)
            db.session.add(nova_relacao)
        
        db.session.commit()
        return {'mensagem': f'{pokemon.nome_pokemon} foi adicionado aos seus favoritos.'}

    @pokemon_ns.doc(security='jsonWebToken')
    @pokemon_ns.response(200, 'Pokémon removido dos favoritos.', modelo_mensagem)
    def delete(self, pokemon_id):
        '''Remove um Pokémon da lista de favoritos do utilizador.'''
        usuario_id = get_jwt_identity()
        
        relacao = PokemonUsuario.query.filter_by(usuario_id=usuario_id, pokemon_id=pokemon_id).first()
        
        if relacao and relacao.favorito:
            relacao.favorito = False
            db.session.commit()
            return {'mensagem': 'Pokémon removido dos favoritos.'}
        
        return {'mensagem': 'Este Pokémon não está na sua lista de favoritos.'}, 404

@pokemon_ns.route('/favoritos')
class ListarFavoritos(Resource):
    method_decorators = [jwt_required()]

    @pokemon_ns.doc(security='jsonWebToken')
    @pokemon_ns.marshal_with(modelo_favoritos_resposta)
    def get(self):
        '''Lista todos os Pokémon favoritos do utilizador logado.'''
        usuario_id = get_jwt_identity()
        
        relacoes = PokemonUsuario.query.filter_by(usuario_id=usuario_id, favorito=True).all()
        
        favoritos_formatado = []
        for relacao in relacoes:
            pokemon = db.session.get(Pokemon, relacao.pokemon_id)
            if pokemon:
                tipo = db.session.get(TipoPokemon, pokemon.tipo_id)
                favoritos_formatado.append({
                    'id': pokemon.id,
                    'nome': pokemon.nome_pokemon,
                    'imagem': pokemon.url_imagem,
                    'tipo': tipo.nome_tipo if tipo else 'N/A',
                })
        
        return {'favoritos': favoritos_formatado}

@pokemon_ns.route('/grupo')
class GrupoBatalha(Resource):
    method_decorators = [jwt_required()]

    @pokemon_ns.doc(security='jsonWebToken')
    @pokemon_ns.expect(modelo_grupo_entrada, validate=True)
    @pokemon_ns.response(200, 'Grupo de batalha atualizado com sucesso', modelo_mensagem)
    def post(self):
        '''Define o grupo de batalha do utilizador a partir dos seus favoritos'''
        data = request.get_json()
        grupo_ids = data.get('grupo')
        usuario_id = get_jwt_identity()

        if not isinstance(grupo_ids, list) or not (0 <= len(grupo_ids) <= 6):
            return {'mensagem': 'Você pode selecionar até 6 Pokémon'}, 400
        
        # Primeiro, limpa o grupo de batalha anterior
        PokemonUsuario.query.filter_by(usuario_id=usuario_id).update({'grupo_batalha': False})

        # Depois, marca os novos Pokémon do grupo
        for pokemon_id in grupo_ids:
            relacao = PokemonUsuario.query.filter_by(
                usuario_id=usuario_id, 
                pokemon_id=pokemon_id, 
                favorito=True
            ).first()

            if not relacao:
                pokemon = db.session.get(Pokemon, pokemon_id) or {'nome_pokemon': f'ID {pokemon_id}'}
                nome = getattr(pokemon, 'nome_pokemon', f'ID {pokemon_id}')
                return {'mensagem': f'O Pokémon {nome} não está na sua lista de favoritos e não pode ser adicionado ao grupo.'}, 400
            
            # Marca a relação existente como parte do grupo de batalha
            relacao.grupo_batalha = True

        db.session.commit()
        return {'mensagem': 'Grupo de batalha atualizado com sucesso'}

    @pokemon_ns.doc(security='jsonWebToken')
    @pokemon_ns.marshal_with(modelo_grupo_resposta)
    def get(self):
        '''Lista o grupo de batalha atual do utilizador'''
        usuario_id = get_jwt_identity()
        relacoes = PokemonUsuario.query.filter_by(usuario_id=usuario_id, grupo_batalha=True).all()
        grupo_formatado = []

        for relacao in relacoes:
            pokemon = db.session.get(Pokemon, relacao.pokemon_id)
            if pokemon:
                tipo = db.session.get(TipoPokemon, pokemon.tipo_id)
                grupo_formatado.append({
                    'id': pokemon.id,
                    'nome': pokemon.nome_pokemon,
                    'imagem': pokemon.url_imagem,
                    'tipo': tipo.nome_tipo if tipo else 'N/A',
                })

        return {'grupo': grupo_formatado}