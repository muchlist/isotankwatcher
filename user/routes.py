from db import mongo

from utils.my_bcrypt import bcrypt
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_refresh_token_required,
    jwt_required,
    get_raw_jwt,
    get_jwt_claims,
)
from marshmallow import ValidationError
from user.user_schema import (
    UserRegisterSchema,
    UserLoginSchema,
    UserChangePassSchema,
    UserEditSchema
)

from datetime import timedelta


EXPIRED_TOKEN = 15

# Set up a Blueprint
bp = Blueprint('user_bp', __name__)

# apakah user eksisting


def user_eksis(username):
    result = mongo.db.users.find_one(
        {"username": username}, {"username": 1})
    return result


@bp.route('/admin/register', methods=['POST'])
@jwt_required
def register_user():
    if request.method == 'POST':

        isAdmin = get_raw_jwt()["user_claims"]["isAdmin"]
        if not isAdmin:
            return {"message": "register hanya dapat dilakukan oleh admin"}, 403

        schema = UserRegisterSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return err.messages, 400

        # mengecek user eksisting
        if user_eksis(data["username"]):
            return {"message": "nama pengguna tidak tersedia"}, 406

        # verifify inputan can be null
        if "email" not in data:
            data["email"] = "nothave@email.com"
        if "phone" not in data:
            data["phone"] = "Tidak terdata"
        if "isAdmin" not in data:
            data["isAdmin"] = False
        if "isAgent" not in data:
            data["isAgent"] = False
        if "isTally" not in data:
            data["isTally"] = False
        if "isForeman" not in data:
            data["isForeman"] = False

        # hash password
        pw_hash = bcrypt.generate_password_hash(
            data["password"]).decode("utf-8")

        data_insert = {
            "username": data["username"].upper(),
            "password": pw_hash,
            "email": data["email"],
            "phone": data["phone"],
            "name": data["name"],
            "isAdmin": data["isAdmin"],
            "isForeman": data["isForeman"],
            "isTally": data["isTally"],
            "isAgent": data["isAgent"],
            "company": data["company"].upper(),
            "position": data["position"],
            "branch": [x.upper() for x in data["branch"]]
        }
        try:
            mongo.db.users.insert_one(data_insert)
        except:
            return {"message": "galat insert register"}, 500

        return {"message": "data berhasil disimpan"}, 201


@bp.route('/admin/users/<string:username>', methods=['PUT', 'DELETE'])
@jwt_required
def user_admin(username):

    isAdmin = get_jwt_claims()["isAdmin"]
    if not isAdmin:
        return {"message": "Edit hanya dapat dilakukan oleh admin"}, 403

    if request.method == 'PUT':
        schema = UserEditSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return err.messages, 400

        if user_eksis(username):
            find = {"username": username}
            update = {
                "name": data["name"],
                "email": data["email"],
                "phone": data["phone"],
                "isAdmin": data["isAdmin"],
                "isAgent": data["isAgent"],
                "isTally": data["isTally"],
                "isForeman": data["isForeman"],
                "branch": [x.upper() for x in data["branch"]],
                "company": data["company"].upper(),
                "position": data["position"]
            }

            mongo.db.users.update_one(find, {'$set': update})

            return {"message": f"user {username} berhasil diubah"}, 201

        return {"message": f"user {username} tidak ditemukan"}, 404

    if request.method == 'DELETE':
        if user_eksis(username):
            mongo.db.users.remove({"username": username})
            return {"message": f"user {username} berhasil dihapus"}, 201
        return {"message": f"user {username} tidak ditemukan"}


@bp.route('/admin/reset/<string:username>', methods=['GET'])
@jwt_required
def reset_password_by_admin(username):

    isAdmin = get_jwt_claims()["isAdmin"]
    if not isAdmin:
        return {"message": "Reset password hanya dapat dilakukan oleh admin"}, 403

    if request.method == 'GET':
        if user_eksis(username):
            # hash password
            pw_hash = bcrypt.generate_password_hash("Password").decode("utf-8")

            find = {"username": username}
            update = {
                "password": pw_hash
            }

            mongo.db.users.update_one(find, {'$set': update})

            return {"message": f"Password user {username} berhasil direset"}, 201

        return {"message": f"user {username} tidak ditemukan"}, 404


@bp.route("/users/<string:username>", methods=['GET'])
@jwt_required
def user(username):
    if request.method == 'GET':
        result = mongo.db.users.find_one(
            {"username": username}, {"password": 0})
        return jsonify(result), 200


@bp.route("/profile", methods=['GET'])
@jwt_required
def show_profile():
    if request.method == 'GET':
        result = mongo.db.users.find_one(
            {"username": get_jwt_identity()}, {"password": 0})
        return jsonify(result), 200


@bp.route("/users", methods=['GET'])
@jwt_required
def user_list():
    if request.method == 'GET':
        user_list = []
        result = mongo.db.users.find({}, {"password": 0})
        for user in result:
            user_list.append(user)

        return jsonify(user_list), 200


@bp.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        schema = UserLoginSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return err.messages, 400

        user = mongo.db.users.find_one({"username": data["username"]})

        # Cek apakah hash password inputan sama
        if user and bcrypt.check_password_hash(user["password"], data["password"]):
            # Membuat akses token menggunakan username di database
            access_token = create_access_token(
                identity=user["username"],
                expires_delta=timedelta(days=EXPIRED_TOKEN),
                fresh=True)
            refresh_token = create_refresh_token(user["username"])
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'name': user['name'],
                'isAdmin': user['isAdmin'],
                'isTally': user['isTally'],
                'isForeman': user['isForeman'],
                'isAgent': user['isAgent'],
                "branch": user["branch"],
                "company": user["company"].upper()
            }, 200

        return {"message": "user atau password salah"}, 400


@bp.route('/change-password', methods=['POST'])
@jwt_required
def change_password():
    schema = UserChangePassSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return err.messages, 400

    user_username = get_jwt_identity()

    user = mongo.db.users.find_one(
        {"username": user_username}, {"password": 1})

    # Cek apakah hash password inputan sama
    if bcrypt.check_password_hash(user["password"], data["password"]):
        # menghash password baru
        inputan_new_password_hash = bcrypt.generate_password_hash(
            data["new_password"]).decode("utf-8")

        query = {"username": user_username}
        update = {'$set': {"password": inputan_new_password_hash}}

        mongo.db.users.update_one(query, update)
        return {'message': "password berhasil di ubah"}, 200

    return {'message': "password salah"}, 400


@bp.route('/refresh', methods=['POST'])
@jwt_refresh_token_required
def refresh_token():
    current_user = get_jwt_identity()
    new_token = create_access_token(
        identity=current_user,
        expires_delta=timedelta(days=EXPIRED_TOKEN),
        fresh=False
    )
    return {'access_token': new_token}, 200


@bp.route('/all-agent', methods=['GET'])
@jwt_required
def get_agent_list():
    all_company_array = mongo.db.users.distinct('company')
    return jsonify(company=all_company_array), 200
