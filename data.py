import pandas as pd

def get_recommendations(user_row, method, users_data, games_data, gamesCategories_data):
    # Obtener datos del usuario
    user_categories = user_row['categories'].split(', ')
    user_years = [int(year.strip()) for year in user_row['release year'].split(', ')]

    # Filtrar juegos por categorías y años
    filtered_games = games_data[
        games_data['app_id'].isin(
            gamesCategories_data[gamesCategories_data['categories'].isin(user_categories)]['app_id']
        )
    ]
    filtered_games['release_date'] = pd.to_datetime(filtered_games['release_date'], errors='coerce')
    filtered_games = filtered_games[filtered_games['release_date'].dt.year.isin(user_years)]

    # Ordenar juegos por el método seleccionado
    if method == 'average':
        filtered_games['score'] = (filtered_games['positive'] - filtered_games['negative']) / filtered_games['price']
    elif method == 'minimum_misery':
        filtered_games['score'] = filtered_games['negative']
    elif method == 'maximum_pleasure':
        filtered_games['score'] = filtered_games['positive']
    else:
        raise ValueError('Método no válido')

    # Ordenar los juegos según el puntaje
    top_games = filtered_games.sort_values('score', ascending=(method == 'minimum_misery')).head(10)

    # Calcular categorías y años más populares
    top_categories = gamesCategories_data[gamesCategories_data['app_id'].isin(top_games['app_id'])]['categories'].value_counts().head(5).index.tolist()
    top_years = top_games['release_date'].dt.year.value_counts().head(5).index.tolist()

    # Encontrar usuarios similares
    similar_users = users_data[
        users_data['categories'].str.contains('|'.join(user_categories))
    ]['user_id'].head(3).tolist()

    return {
        'top_games': top_games['name'].tolist(),
        'top_categories': top_categories,
        'top_years': top_years,
        'similar_users': similar_users
    }
