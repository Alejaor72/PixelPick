from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter

# Iniciar Flask app
app = Flask(__name__)
CORS(app)  # Para permitir las solicitudes desde el frontend (React)

# Función para cargar datasets
def cargar_datasets():
    try:
        dataNetflix = pd.read_csv("datasets/dataNetflix.csv")
        dataPrime = pd.read_csv("datasets/dataPrime.csv")
        dataHbo = pd.read_csv("datasets/dataHbo.csv")
        return dataNetflix, dataPrime, dataHbo
    except Exception as e:
        print(f"Error al cargar los datasets: {e}")
        return None, None, None

# Función para generar el usuario ficticio
def generar_usuario_ficticio(respuestas):
    try:
        print("Respuestas recibidas:", respuestas)  # Imprimir las respuestas recibidas

        # Validación para asegurarse de que las respuestas no estén vacías
        if not respuestas:
            raise ValueError("No se recibieron respuestas válidas.")

        # Obtener la plataforma más frecuente
        plataformas = [plataforma for r in respuestas for plataforma in r["plataformas"]]
        if not plataformas:
            raise ValueError("No se seleccionaron plataformas.")
        
        plataforma_moda = Counter(plataformas).most_common(1)[0][0]
        
        # Obtener los géneros únicos
        generos = list(set.union(*[set(r["generos"].split(',')) for r in respuestas if r["generos"]]))
        if not generos:
            raise ValueError("No se proporcionaron géneros válidos.")
        
        # Obtener el formato más frecuente
        formatos = [r["formato"] for r in respuestas if r["formato"]]
        if not formatos:
            raise ValueError("No se proporcionaron formatos válidos.")
        
        formato = max(set(formatos), key=formatos.count)

        # Calcular la calificación mínima promedio
        calificaciones = [r["calificacion_minima"] for r in respuestas if isinstance(r["calificacion_minima"], (int, float))]
        if not calificaciones:
            raise ValueError("No se proporcionaron calificaciones mínimas válidas.")
        
        calificacion_minima = sum(calificaciones) / len(calificaciones)

        # Calcular el rango de años
        anios_desde = [int(r["rango_anios"]["desde"]) for r in respuestas if r["rango_anios"]["desde"]]
        anios_hasta = [int(r["rango_anios"]["hasta"]) for r in respuestas if r["rango_anios"]["hasta"]]
        if not anios_desde or not anios_hasta:
            raise ValueError("No se proporcionaron años válidos.")
        
        rango_anios = (min(anios_desde), max(anios_hasta))

        print("Usuario ficticio generado:", {
            "plataforma_moda": plataforma_moda,
            "generos": generos,
            "formato": formato,
            "calificacion_minima": calificacion_minima,
            "rango_anios": rango_anios
        })

        return {
            "plataforma_moda": plataforma_moda,
            "generos": generos,
            "formato": formato,
            "calificacion_minima": calificacion_minima,
            "rango_anios": rango_anios
        }
    except Exception as e:
        print(f"Error al generar el usuario ficticio: {e}")
        return {"error": str(e)}



# Función para cargar dataset basado en la plataforma moda
def cargar_dataset_por_plataforma(plataforma):
    try:
        if plataforma == "Netflix":
            return pd.read_csv("datasets/dataNetflix.csv")
        elif plataforma == "Prime":
            return pd.read_csv("datasets/dataPrime.csv")
        elif plataforma == "HBO":
            return pd.read_csv("datasets/dataHbo.csv")
        else:
            raise ValueError("Plataforma no soportada")
    except Exception as e:
        print(f"Error al cargar el dataset para {plataforma}: {e}")
        return None

# Función para preparar dataset para vectorización
def preparar_datos_para_vectorizacion(dataset):
    dataset['genres'] = dataset['genres'].fillna('')
    dataset['type'] = dataset['type'].fillna('')
    dataset['releaseYear'] = dataset['releaseYear'].fillna(0).astype(int)

    # Crear columna combinada
    dataset['combined_features'] = (
        dataset['genres'] + ' ' +
        dataset['type'] + ' ' +
        dataset['releaseYear'].astype(str)
    )
    return dataset

# Función para generar recomendaciones usando similitud coseno
def recomendar_con_coseno_y_knn(dataset, usuario_ficticio, k=10):
    dataset = preparar_datos_para_vectorizacion(dataset)

    # Filtrar dataset según las preferencias del usuario ficticio
    dataset_filtrado = dataset[
        (dataset['type'] == usuario_ficticio['formato']) &
        (dataset['imdbAverageRating'] >= usuario_ficticio['calificacion_minima']) &
        (dataset['releaseYear'] >= usuario_ficticio['rango_anios'][0]) &
        (dataset['releaseYear'] <= usuario_ficticio['rango_anios'][1])
    ]

    if dataset_filtrado.empty:
        return []

    # Vectorizar dataset filtrado
    vectorizer = CountVectorizer()
    vectors = vectorizer.fit_transform(dataset_filtrado['combined_features']).toarray()

    # Crear vector de preferencias del usuario ficticio
    print("Generos:", usuario_ficticio['generos'])
    print("Formato:", usuario_ficticio['formato'])
    print("Rango años:", usuario_ficticio['rango_anios'])

    user_preferences = (
      ' '.join(usuario_ficticio['generos']) + ' ' +
      usuario_ficticio['formato'] + ' ' +
      ' '.join([str(año) for año in range(int(usuario_ficticio['rango_anios'][0]), int(usuario_ficticio['rango_anios'][1]) + 1)])
    )

    user_vector = vectorizer.transform([user_preferences]).toarray()

    # Calcular la similitud coseno
    cosine_similarities = cosine_similarity(user_vector, vectors)
    similar_indices = cosine_similarities[0].argsort()[-k:][::-1]

    recomendaciones = dataset_filtrado.iloc[similar_indices]
    recomendaciones['similarity_score'] = cosine_similarities[0][similar_indices]
    recomendaciones = recomendaciones.sort_values('similarity_score', ascending=False)

    return recomendaciones[['title', 'releaseYear', 'similarity_score']].to_dict(orient='records')

# Ruta para recibir las respuestas del frontend y devolver recomendaciones
@app.route('/recomendar', methods=['POST'])
def recomendar():
    try:
        data = request.json
        respuestas = data['respuestas']

        usuario_ficticio = generar_usuario_ficticio(respuestas)
        dataset_seleccionado = cargar_dataset_por_plataforma(usuario_ficticio["plataforma_moda"])

        if dataset_seleccionado is not None:
            recomendaciones = recomendar_con_coseno_y_knn(dataset_seleccionado, usuario_ficticio, k=5)
            return jsonify({'recomendaciones': recomendaciones})

        return jsonify({'recomendaciones': []})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Iniciar servidor
if __name__ == '__main__':
    app.run(debug=True)
