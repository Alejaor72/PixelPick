import pandas as pd
from flask import Flask, request, jsonify, render_template
from data import get_recommendations

app = Flask(__name__, static_url_path='/static')

# URL del Google Sheet
USERS_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRr-tTsgc4OvNS8FBG6iVafgYSSeKgtezk1b9oo6FH-209dTpx1yuXbaW3sGh6Xzbp-RYHjaMR9Y-9V/pub?output=csv"

# Cargar datos estáticos
games_data = pd.read_csv('./datasets/games.csv')
gamesCategories_data = pd.read_csv('./datasets/t-games-categories.csv')

def load_users_data():
    """
    Cargar los datos de usuarios desde Google Sheets.
    """
    try:
        return pd.read_csv(USERS_SHEET_URL)
    except Exception as e:
        print(f"Error al cargar usuarios: {e}")
        raise

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/users', methods=['GET'])
def get_users():
    """
    Endpoint para obtener los usuarios disponibles desde Google Sheets.
    """
    try:
        users_data = load_users_data()
        print(users_data.head())  # Verificar los datos cargados
        users = users_data[['user_id']].to_dict(orient='records')
        return jsonify(users)
    except Exception as e:
        print(f"Error en /users: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/recommend', methods=['GET'])
def recommend():
    """
    Endpoint para obtener recomendaciones basadas en usuario y método.
    """
    user_id = request.args.get('user_id')
    method = request.args.get('method', 'average')

    if not user_id:
        return jsonify({"error": "user_id es requerido"}), 400

    try:
        # Cargar datos dinámicamente
        users_data = load_users_data()

        # Verificar si el usuario existe
        user_row = users_data[users_data['user_id'] == user_id]
        if user_row.empty:
            return jsonify({"error": "Usuario no encontrado"}), 404

        # Obtener recomendaciones
        user_row = user_row.iloc[0]
        recommendations = get_recommendations(user_row, method, users_data, games_data, gamesCategories_data)
        return jsonify(recommendations)
    except Exception as e:
        print(f"Error en /recommend: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
