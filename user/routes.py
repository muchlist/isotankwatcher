from db import mongo

from utils.my_bcrypt import bcrypt
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_refresh_token_required,
    jwt_required,
    get_raw_jwt
)
from marshmallow import ValidationError
from user.user_schema import UserSchema


# Set up a Blueprint
bp = Blueprint('user_bp', __name__)


def user_eksis(username):
    result = mongo.db.users.find_one(
        {"username": username}, {"username": 1})
    return result


@bp.route('/register', methods=['POST'])
def register_user():
    if request.method == 'POST':
        user_scm = UserSchema()
        try:
            data = user_scm.load(request.get_json())
        except ValidationError as err:
            return err.messages, 400

        if "email" not in data:
            data["email"] = "nothave@email.com"

        # mengecek user eksisting
        if user_eksis(data["username"]):
            return {"message": "nama pengguna tidak tersedia"}, 400

        # hash password
        pw_hash = bcrypt.generate_password_hash(
            data["password"]).decode("utf-8")

        mongo.db.users.insert_one(
            {"username": data["username"], "password": pw_hash, "email": data["email"]})
        return {"message": "data berhasil disimpan"}, 201


@bp.route('/user/<string:name>', methods=['GET'])
def mencari_user(name):
    if request.method == 'GET':
        result = mongo.db.users.find_one(
            {"username": name}, {"password": 0})
        return jsonify(result), 200


@bp.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()

        user = mongo.db.users.find_one({"username": data["username"]})

        print(user)

        # Cek apakah hash password inputan sama
        if user and bcrypt.check_password_hash(user["password"], data["password"]):
            # Membuat akses token menggunakan username di database
            access_token = create_access_token(
                identity=user["username"],
                fresh=True)
            refresh_token = create_refresh_token(user["username"])
            return {
                'access_token': access_token,
                'refresh_token': refresh_token
            }, 200

        return {"message": "user atau password salah"}, 400


@bp.route('/refresh', methods=['POST'])
@jwt_refresh_token_required
def refresh_token():
    current_user = get_jwt_identity()
    new_token = create_access_token(identity=current_user, fresh=False)
    return {'access_token': new_token}, 200
