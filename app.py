import pandas as pd
from flask import Flask, request, jsonify, render_template
from data import get_recommendations

app = Flask(__name__)

# Cargar datos
games_data = pd.read_csv('./datasets/games.csv')
gamesCategories_data = pd.read_csv('./datasets/t-games-categories.csv')
users_data = pd.read_csv('./static/users.csv')

@app.route('/')
def home():
    # Renderiza el HTML principal
    return render_template('index.html')

@app.route('/users', methods=['GET'])
def get_users():
    """
    Endpoint para obtener los usuarios disponibles.
    """
    try:
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
