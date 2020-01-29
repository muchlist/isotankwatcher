import os

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_uploads import configure_uploads, patch_request_class

from db import mongo
from utils.my_encoder import JSONEncoder
from utils.my_bcrypt import bcrypt
from user.routes import bp as user_bp
from container.routes import bp as container_bp
from vessel.routes import bp as vessel_bp
from container_image.routes import bp as container_image_bp
from utils.image_helper import IMAGE_SET

app = Flask(__name__)
app.config.from_object('config.Config')
# app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
# app.config["UPLOADED_IMAGES_DEST"] = os.environ.get("UPLOADED_IMAGES_DEST")
# app.config["JWT_SECRET_KEY "] = os.environ.get("SECRET_KEY")
# app.secret_key = os.environ.get("SECRET_KEY")
patch_request_class(app, 6 * 1024 * 1024)  # 6MB max upload
configure_uploads(app, IMAGE_SET)

mongo.init_app(app)
bcrypt.init_app(app)
jwt = JWTManager(app)

# ENCODER jsonify untuk menghandle objectID dan Datetime dari mongodb
app.json_encoder = JSONEncoder


@jwt.user_claims_loader
def add_claims_to_jwt(identity):
    user = mongo.db.users.find_one({"username": identity})
    return {"name": user["name"],
            "isAdmin": user["isAdmin"],
            "isTally": user["isTally"],
            "isForeman": user["isForeman"],
            "isAgent": user["isAgent"],
            "branch": user["branch"],
            "company": user["company"]}


app.register_blueprint(user_bp)
app.register_blueprint(container_bp)
app.register_blueprint(vessel_bp)
app.register_blueprint(container_image_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
