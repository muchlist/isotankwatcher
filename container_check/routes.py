from db import mongo

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
    get_jwt_claims,
)
from marshmallow import ValidationError
from bson.objectid import ObjectId

from container_check.container_check_schema import (
    ContainerCheckInitSchema,
    ContainerCheckEditSchema,
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
    switch = {
        "one": 1,  # 1 info container init , 2 check one created, 3 check one finish
        "two": 3,  # 4 check two created, 5 check two finish
        "three": 5,  # 6 check three created, 7 check three finish
        "four": 7,  # 8 check four created, 9 check four dinish document finish
    }
    query = {
        '_id': ObjectId(container_id),
        'document_level': switch.get(step)
    }
    update = {
        # Memasukkan ID check dan Status dan Note Pengecekan ke Container Info
        '$set': {f"checkpoint.{step.lower()}": f"{container_id}-{step.lower()}",
                 f"checkpoint_status.{step.lower()}": f'{data["status"]} : {data["note"]}'},
        '$inc': {"document_level": 1}
    }
    try:
        container_info = mongo.db.container_info.find_one_and_update(
            query, update, return_document=True)
    except:
        return {"message": "galat insert pada container_info"}, 500

    if container_info is None:
        return {"message": "container id atau step update salah"}, 400
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
        "foreman": "",
        "foreman_name": "",
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
        "position_step": step.lower(),
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
Container Check list, GET
hanya mengembalikan list check lvl 2 (yang mana belum diapprove oleh foreman)
-------------------------------------------------------------------------------
"""
@bp.route('/checks', methods=['GET'])
@jwt_required
def get_check_container_list():
    claims = get_jwt_claims()
    if request.method == 'GET':

        """ 
        ?branch=SAMPIT    
        &  doc_level=2 
        """

        branch = request.args.get("branch")

        # find database
        find = {}
        find["doc_level"] = 2
        if branch:
            find["container.branch"] = branch

        container_check_coll = mongo.db.container_check.find(
            find).sort("updated_at", -1)
        container_check_list = []

        for container_check in container_check_coll:
            container_check_list.append(container_check)

        return {"container_checks": container_check_list}, 200


"""
-------------------------------------------------------------------------------
Detail Check Container, GET PUT
-------------------------------------------------------------------------------
"""
@bp.route('/check/<check_id>', methods=['GET', 'PUT'])
@jwt_required
def get_detail_check_container(check_id):

    if request.method == "GET":
        container_check = mongo.db.container_check.find_one(
            {'_id': check_id})
        return jsonify(container_check), 200

    if request.method == "PUT":
        schema = ContainerCheckEditSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return err.messages, 400

        claims = get_jwt_claims()
        if not claims["isTally"]:
            return {"message": "user tidak memiliki hak akses untuk menambahkan data"}, 403

        query = {
            '_id': check_id,
            'updated_at': data["updated_at"],
            'doc_level': 1,
            'container.branch': claims["branch"][0]
        }
        update = {
            '$set': {
                'checked_at': data["checked_at"],
                'note': data["note"],
                'status': data["status"],
                'witness': data["witness"],
                'updated_at': datetime.now()
            }
        }
        try:
            #Update container check
            container_check = mongo.db.container_check.find_one_and_update(
                query, update, return_document=True)
        except:
            return {"message": "galat insert pada container_info"}, 500

        if container_check == None:
            return {"message": "Gagal update. Dokumen ini telah di ubah oleh seseorang sebelumnya. Harap cek data terbaru!"}, 402
        else:
            # Container Check Berhasil diubah, Container Info juga Perlu di ubah
            query = {
                '_id': ObjectId(container_check["container_id"])
            }
            update = {'$set':
                      {f'checkpoint_status.{container_check["position_step"]}':
                          f'{container_check["status"]} : {container_check["note"]}'}
                      }
            try:
                mongo.db.container_info.find_one_and_update(
                    query, update, return_document=False)
            except:
                return {"message": "galat update pada container_info"}, 500
        return jsonify(container_check), 201


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
        return receiving_muat.get(step.lower())
    elif activity == "BONGKAR-DELIVERY":
        return bongkar_delivery.get(step.lower())
    else:
        return None
