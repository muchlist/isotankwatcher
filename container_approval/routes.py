from db import mongo

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
    get_jwt_claims,
)
from marshmallow import ValidationError
from bson.objectid import ObjectId

from container_approval.container_approval_schema import ContainerApprovalSchema

from datetime import datetime


# Set up a Blueprint
bp = Blueprint('container_approval_bp', __name__, url_prefix='/api')


"""
-------------------------------------------------------------------------------
APPROVAL dari Tally dari lvl 1 ke lvl 2
-------------------------------------------------------------------------------
"""
@bp.route('/check/<check_id>/ready', methods=['POST'])
@jwt_required
def check_to_ready_doc(check_id):

    claims = get_jwt_claims()

    if not claims["isTally"]:
        return {"message": "User tidak memiliki hak akses untuk merubah dokumen ini"}, 403

    schema = ContainerApprovalSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return err.messages, 400

    query = {
        '_id': check_id,
        "updated_at": data["updated_at"],
        "doc_level": 1,
        "container.branch": claims["branch"][0]
    }
    print(query)
    update = {
        '$set': {"doc_level": 2,
                 "approval.checked_by": get_jwt_identity(),
                 "approval.checked_by_name": claims["name"],
                 "updated_at": datetime.now()}
    }

    # DATABASE
    container_check = mongo.db.container_check.find_one_and_update(
        query, update, return_document=True
    )

    if container_check is None:
        return {"message": "Gagal update. Dokumen ini telah di ubah oleh seseorang sebelumnya. Harap cek data terbaru!"}, 402

    return jsonify(container_check), 201


"""
-------------------------------------------------------------------------------
Batal APPROVAL dari Tally dari ke lvl 2 ke lvl 1
-------------------------------------------------------------------------------
"""
@bp.route('/check/<check_id>/unready', methods=['POST'])
@jwt_required
def check_to_unready_doc(check_id):

    claims = get_jwt_claims()

    if not claims["isTally"]:
        return {"message": "User tidak memiliki hak akses untuk merubah dokumen ini"}, 403

    schema = ContainerApprovalSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return err.messages, 400

    query = {
        '_id': check_id,
        "updated_at": data["updated_at"],
        "doc_level": 2,
        "container.branch": claims["branch"][0]
    }
    update = {
        '$set': {"doc_level": 1,
                 "approval.checked_by": get_jwt_identity(),
                 "approval.checked_by_name": claims["name"],
                 "updated_at": datetime.now()}
    }

    # DATABASE
    container_check = mongo.db.container_check.find_one_and_update(
        query, update, return_document=True
    )

    if container_check is None:
        return {"message": "Gagal update. Dokumen ini telah di ubah oleh seseorang sebelumnya. Harap cek data terbaru!"}, 402

    return jsonify(container_check), 201


"""
-------------------------------------------------------------------------------
APPROVAL dari Foreman dari ke lvl 2 ke lvl 3
-------------------------------------------------------------------------------
"""
@bp.route('/check/<check_id>/approval', methods=['POST'])
@jwt_required
def approval_foreman_doc(check_id):

    claims = get_jwt_claims()

    if not claims["isForeman"]:
        return {"message": "User tidak memiliki hak akses untuk mengapprove dokumen ini"}, 403

    schema = ContainerApprovalSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return err.messages, 400

    query = {
        '_id': check_id,
        "updated_at": data["updated_at"],
        "doc_level": 2,
        "container.branch": claims["branch"][0]
    }
    update = {
        '$set': {"doc_level": 3,
                 "approval.foreman": get_jwt_identity(),
                 "approval.foreman_name": claims["name"],
                 "updated_at": datetime.now()}
    }

    # DATABASE
    container_check = mongo.db.container_check.find_one_and_update(
        query, update, return_document=True
    )

    if container_check is None:
        return {"message": "Gagal update. Dokumen ini telah di ubah oleh seseorang sebelumnya. Harap cek data terbaru!"}, 402
    else:
        #CEK APAKAH STATUS TIDAK SAMA DENGAN NIHIL
        dammaged = container_check["status"] != "NIHIL"
        lvl_up_container_info_lvl(container_check["container_id"], dammaged)

    # if container_check["position_step"] == "four":
    #     # TODO BIKIN PDF

    return jsonify(container_check), 201


def lvl_up_container_info_lvl(container_id, dammaged):
    query = {'_id': ObjectId(container_id)}
    update = {'$inc': {"document_level": 1}}
    
    if dammaged:
        update["dammaged"] = True

    try:
        mongo.db.container_info.find_one_and_update(
            query, update, return_document=False)
    except:
        return {"message": "galat menaikkan lvl pada container_info"}, 500
