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

# Endpoint: Service de recherche
@app.route('/search', methods=['GET'])
@require_auth
def search_quotes():
    """
    Rechercher des citations par mot-clé
    ---
    security:
      - APIKeyAuth: []
    parameters:
      - name: keyword
        in: query
        required: true
        type: string
    responses:
      200:
        description: Liste des citations correspondantes
    """
    keyword = request.args.get("keyword")

    if not keyword:
        return jsonify({"error": "Mot-clé requis"}), 400

    members = redis_client.smembers("quotes")
    filtered_quotes = []
    for member in members:
        quote_object = redis_client.hgetall(member)
        quote = quote_object.get("quote","")
        if keyword.lower() in quote.lower():
            filtered_quotes.append(quote)
    return jsonify(filtered_quotes), 200

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_key = request.headers.get("Authorization")
        if not auth_key or auth_key != ADMIN_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/search/docs', methods=['GET'])
def get_search_api_docs():
    """
    Endpoint pour accéder à la documentation de l'API de recherche
    ---
    responses:
      200:
        description: Documentation de l'API de recherche en Swagger
    """
    return jsonify({
        "swagger": "2.0",
        "info": {
            "title": "Search Quotes API",
            "description": "API permettant de rechercher des citations par mot-clé.",
            "version": "1.0.0"
        },
        "basePath": "/",
        "paths": {
            "/search": {
                "get": {
                    "summary": "Rechercher des citations par mot-clé",
                    "operationId": "searchQuotes",
                    "parameters": [
                        {
                            "name": "keyword",
                            "in": "query",
                            "description": "Mot-clé pour rechercher des citations",
                            "required": True,
                            "type": "string"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Liste des citations correspondantes"
                        },
                        "400": {
                            "description": "Mot-clé requis"
                        }
                    }
                }
            }
        }
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=APP_PORT)