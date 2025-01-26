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


CSV_FILE_USERS = os.getenv("CSV_FILE", "initial_data_users.csv")

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
if not redis_client.exists("users"):
    if os.path.exists(CSV_FILE_USERS):
        with open(CSV_FILE_USERS, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                id=row['id']
                name=row['name']
                password=row['password']
                redis_client.hset(f"users:{id}", mapping={"id": id,"name": name, "password": password})
                redis_client.sadd("users",f"users:{id}")

# Endpoint: Service des utilisateurs
@app.route('/users', methods=['GET'])
@require_auth
def get_users():
    """
    Récupérer la liste des utilisateurs
    ---
    security:
      - APIKeyAuth: []
    responses:
      200:
        description: Liste des utilisateurs
    """
    users_ids = redis_client.smembers("users")
    users=[]
    for user_id in users_ids:
        users.append(redis_client.hgetall(user_id))
    print(users)
    return jsonify(users), 200

@app.route('/users', methods=['POST'])
@require_auth
def add_user():
    """
    Ajouter un utilisateur
    ---
    security:
      - APIKeyAuth: []
    parameters:
      - name: user
        in: body
        required: true
        schema:
          type: object
          properties:
            id:
              type: string
            name:
              type: string
            password:
              type: string
    responses:
      201:
        description: Utilisateur ajouté
    """
    data = request.get_json()
    user_id = data.get("id")
    name = data.get("name")
    password = data.get("password")

    if not user_id or not name:
        return jsonify({"error": "ID et nom sont requis"}), 400

    redis_client.hset(f"users:{user_id}", mapping={"id": user_id,"name": name, "password": password})
    redis_client.sadd("users",f"users:{user_id}")
    return jsonify({"message": "Utilisateur ajouté"}), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=APP_PORT)