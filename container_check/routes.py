from db import mongo

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
from bson.objectid import ObjectId

from container_check.container_check_schema import (
    ContainerCheckInitSchema,
)

from datetime import datetime
import string

# Set up a Blueprint
bp = Blueprint('container_check_bp', __name__, url_prefix='/api')

"""
-------------------------------------------------------------------------------
Create Check Container Position
-------------------------------------------------------------------------------
"""
@bp.route('/create-check/<container_id>/<step>', methods=['POST'])
@jwt_required
def create_check_container(container_id, step):

    claims = get_jwt_claims()

    if not ObjectId.is_valid(container_id):
        return {"message": "Object ID tidak valid"}, 400

    if not step in ("one", "two", "three", "four"):
        return {"message": "step harus diantara one, two, three, four"}, 400

    schema = ContainerCheckInitSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return err.messages, 400

    if not claims["isTally"]:
        return {"message": "user tidak memiliki hak akses untuk menambahkan data"}, 403

    # DATABASE CONTAINER_INFO BEGIN
    query = {
        '_id': ObjectId(container_id)
    }
    update = {
        '$set': {f"checkpoint.{step}": f"{container_id}-{step}"}
    }
    try:
        container_info = mongo.db.container_info.find_one_and_update(
            query, update, return_document=True)
    except:
        return {"message": "galat insert pada container_info"}, 500

    if container_info is None:
        return {"message": "container id salah"}, 400
    # DATABASE END

    computed_position = translate_step(container_info["activity"], step)
    container_data_embed = {
        "branch": container_info["branch"],
        "container_number": container_info["container_number"],
        "agent": container_info["agent"],
        "activity": container_info["activity"]
    }
    approval_data_embed = {
        "checked_by": get_jwt_identity(),
        "checked_by_name": claims["name"],
        "approval_foreman": "",
        "approval_foreman_name": "",
        "witness": data["witness"],
        "witness_note": ""
    }
    image_embed = {
        "url_img_back": "",
        "url_img_bottom": "",
        "url_img_front": "",
        "url_img_left": "",
        "url_img_right": "",
        "url_img_up": "",
        "url_img_witness": ""
    }
    data_insert = {
        "_id": f"{container_id}-{step}",
        "container_id": container_id,
        "container": container_data_embed,
        "updated_at": datetime.now(),
        "position":  computed_position,
        "checked_at": data["checked_at"],
        "note": data["note"],
        "status": data["status"],
        "image":  image_embed,
        "approval": approval_data_embed,
        "doc_level": 1,
    }

    # DATABASE container check BEGIN
    try:
        mongo.db.container_check.insert_one(data_insert)
    except:
        return {"message": "galat insert container_check, kemungkinan data sudah ada"}, 500
    # DATABASE container check END

    return jsonify(data_insert), 201


"""
-------------------------------------------------------------------------------
Detail Check Container, GET PUT
-------------------------------------------------------------------------------
"""
@bp.route('/check/<check_id>', methods=['GET', 'PUT'])
@jwt_required
def get_detail_check_container(check_id):

    if request.method == "GET":
        claims = get_jwt_claims()

        container_check = mongo.db.container_check.find_one(
            {'_id': check_id})
        return jsonify(container_check), 200

    #TODO PUT


def translate_step(activity, step):
    receiving_muat = {"one": "GATE IN",
                      "two": "STACK",
                      "three": "UNSTACK",
                      "four": "DERMAGA"}
    bongkar_delivery = {"one": "DERMAGA",
                        "two": "STACK",
                        "three": "UNSTACK",
                        "four": "GATE OUT"}
    if activity == "RECEIVING-MUAT":
        return receiving_muat[step]
    elif activity == "BONGKAR-DELIVERY":
        return bongkar_delivery[step]
    else:
        return None
