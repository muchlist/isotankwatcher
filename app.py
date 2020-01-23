import os
from dotenv import load_dotenv

from flask import Flask
from flask_jwt_extended import JWTManager

from db import mongo
from utils.my_encoder import JSONEncoder
from utils.my_bcrypt import bcrypt
from user.routes import bp as user_bp
from container.routes import bp as container_bp
from vessel.routes import bp as vessel_bp

load_dotenv('.env')

app = Flask(__name__)
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
#app.config['JWT_BLACKLIST_ENABLED'] = True
#app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
app.secret_key = os.environ.get("SECRET_KEY")

bcrypt.init_app(app)
jwt = JWTManager(app)

# ENCODER jsonify untuk menghandle objectID dan Datetime dari mongodb
app.json_encoder = JSONEncoder


@jwt.user_claims_loader
def add_claims_to_jwt(identity):
    user = mongo.db.users.find_one({"username": identity})
    return {"isAdmin": user["isAdmin"],
            "isForeman": user["isForeman"],
            "isAgent": user["isAgent"],
            "branch": user["branch"]}


app.register_blueprint(user_bp)
app.register_blueprint(container_bp)
app.register_blueprint(vessel_bp)

if __name__ == '__main__':
    mongo.init_app(app)
    app.run(port=5000, debug=True)
