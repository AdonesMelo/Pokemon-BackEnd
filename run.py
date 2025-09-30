from app import create_app
from app.pokemon.routes import garantir_pokemon_no_db
from app.extensions import db

app = create_app()

# --- SCRIPT DE POPULAÇÃO (TEMPORÁRIO) ---
@app.cli.command('popular-db')
def popular_db_command():
    '''Carrega os primeiros 151 Pokémon na base de dados.'''
    print('A popular a base de dados com a Geração 1 de Pokémon...')
    with app.app_context():
        for i in range(1, 152):
            garantir_pokemon_no_db(i)
    print('Base de dados populada com sucesso!')
# ------------------------------------

if __name__ == '__main__':
    app.run(debug=True)