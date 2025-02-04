import os
import csv
from flask import Flask, request, jsonify
from redis import Redis
from flasgger import Swagger
from functools import wraps
import base64

# Configuration des variables d'environnement
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
APP_PORT = int(os.getenv("APP_PORT", 5000))


CSV_FILE_QUOTES = os.getenv("CSV_FILE", "initial_data_quotes.csv")

# Initialisation de Flask et Swagger
app = Flask(__name__)
swagger = Swagger(app)

# Connexion à Redis
redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

def authenticate_user(username, password):
    """Authentifie un utilisateur avec nom et mot de passe."""
    users = redis_client.smembers("users")
    for user_id in users:
        user = redis_client.hgetall(user_id)
        if user.get("name") == username and user.get("password") == password:
            return True
    return False

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        # Décoder l'authentification Basic
        try:
            auth_decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
            username, password = auth_decoded.split(":", 1)
        except (ValueError, base64.binascii.Error):
            return jsonify({"error": "Invalid Authorization format"}), 401

        if not authenticate_user(username, password):
            return jsonify({"error": "Unauthorized"}), 401

        # Authentification réussie
        return f(*args, **kwargs)

    return decorated

# Chargement initial des données
if not redis_client.exists("quotes:1"):
    if os.path.exists(CSV_FILE_QUOTES):
        with open(CSV_FILE_QUOTES, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
               quote=row['quote']
               quote_id = redis_client.incr("quote_id")
               redis_client.hset(f"quotes:{quote_id}", mapping={"quote": quote})
               redis_client.sadd("quotes",f"quotes:{quote_id}")

# Endpoint: Service des citations
@app.route('/quotes', methods=['GET'])
def get_quotes():
    """
    Récupérer toutes les citations
    ---
    security:
      - APIKeyAuth: []
    responses:
      200:
        description: Liste des citations
    """
    quotes = redis_client.smembers("quotes")
    quote_list=[]
    for quote in quotes:
        quote_list.append(redis_client.hgetall(quote))
    return jsonify(quote_list), 200

@app.route('/quotes', methods=['POST'])
@require_auth
def add_quote():
    """
    Ajouter une citation
    ---
    security:
      - APIKeyAuth: []
    parameters:
      - name: quote
        in: body
        required: true
        schema:
          type: object
          properties:
            user_id:
              type: string
            quote:
              type: string
    responses:
      201:
        description: Citation ajoutée
    """
    data = request.get_json()
    user_id = data.get("user_id")
    quote = data.get("quote")

    if not user_id or not quote:
        return jsonify({"error": "user_id et quote sont requis"}), 400

    quote_id = redis_client.incr("quote_id")
    redis_client.hset("quotes", quote_id, str({"user_id": user_id, "quote": quote}))
    return jsonify({"message": "Citation ajoutée", "id": quote_id}), 201

@app.route('/quotes/<int:quote_id>', methods=['DELETE'])
@require_auth
def delete_quote(quote_id):
    """
    Supprimer une citation par ID
    ---
    security:
      - APIKeyAuth: []
    parameters:
      - name: quote_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Citation supprimée
      404:
        description: Citation non trouvée
    """
    if not redis_client.hexists(f"quotes:{quote_id}","quote"):
        return jsonify({"error": "Citation non trouvée"}), 404

    redis_client.hdel(f"quotes:{quote_id}","quote")
    return jsonify({"message": "Citation supprimée"}), 200
  
@app.route('/quotes/docs', methods=['GET'])
def get_api_docs():
    """
    Endpoint pour accéder à la documentation de l'API
    ---
    responses:
      200:
        description: Documentation de l'API en Swagger
    """
    return jsonify({
        "swagger": "2.0",
        "info": {
            "title": "Quotes API",
            "description": "API permettant de gérer des citations.",
            "version": "1.0.0"
        },
        "basePath": "/",
        "paths": {
            "/quotes": {
                "get": {
                    "summary": "Récupérer toutes les citations",
                    "operationId": "getQuotes",
                    "responses": {
                        "200": {
                            "description": "Liste des citations"
                        }
                    }
                },
                "post": {
                    "summary": "Ajouter une citation",
                    "operationId": "addQuote",
                    "parameters": [
                        {
                            "name": "quote",
                            "in": "body",
                            "description": "Citation à ajouter",
                            "required": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "user_id": {
                                        "type": "string"
                                    },
                                    "quote": {
                                        "type": "string"
                                    }
                                }
                            }
                        }
                    ],
                    "responses": {
                        "201": {
                            "description": "Citation ajoutée"
                        }
                    }
                }
            },
            "/quotes/{quote_id}": {
                "delete": {
                    "summary": "Supprimer une citation",
                    "operationId": "deleteQuote",
                    "parameters": [
                        {
                            "name": "quote_id",
                            "in": "path",
                            "description": "ID de la citation à supprimer",
                            "required": True,
                            "type": "integer"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Citation supprimée"
                        },
                        "404": {
                            "description": "Citation non trouvée"
                        }
                    }
                }
            }
        }
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=APP_PORT)