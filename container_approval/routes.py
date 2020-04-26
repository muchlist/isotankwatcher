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
from utils import generate_pdf as gl


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
APPROVAL Witness , weak approval , jika sudah semua android di update,
ganti approval tally untuk mengharuskan witness approved True terlebih dulu
-------------------------------------------------------------------------------
"""
@bp.route('/check/<check_id>/witness-approve', methods=['POST'])
@jwt_required
def check_to_witness_approval(check_id):

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
    update = {
        '$set': {"approval.witness_approved": True,
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
        # CEK APAKAH STATUS TIDAK SAMA DENGAN NIHIL
        dammaged = container_check["status"] != "NIHIL"
        # CEK APAKAH PAKSA Container Info KE LVL 9, "BONGKAR-DELIVERY  - Step three"
        forced = forced_to_finish(
            container_check["container"]["activity"], container_check["position_step"])
        container_info = lvl_up_container_info_lvl(
            container_check["container_id"], dammaged, forced)

        # MEMBUAT PDF START
        try:
            gl.generate_pdf(container_info, container_check)
        except:
            return {"message": "Gagal membuat pdf!"}, 403
        # MEMBUAT PDF END

    return jsonify(container_check), 201


"""
-------------------------------------------------------------------------------
TESTING PDF
-------------------------------------------------------------------------------
"""
@bp.route('/testingpdf/<container_id>/<check_id>', methods=['GET'])
@jwt_required
def approval_test_pdf():
    container_check = mongo.db.container_check.find_one({'_id': check_id})
    container_info = mongo.db.container_info.find_one({'_id': ObjectId(container_id)})
    gl.generate_pdf(container_info, container_check)
    return jsonify(container_check), 201


def lvl_up_container_info_lvl(container_id, dammaged, forced_lvl):
    query = {'_id': ObjectId(container_id)}
    update = {'$inc': {"document_level": 1}}
    set_embed = {'updated_at': datetime.now()}
    if forced_lvl:
        update = {}  # jika force maka hilangakan increment
        set_embed["document_level"] = 9  # tindih dengan naik langsung ke lvl 9
    if dammaged:
        set_embed["dammaged"] = True
    
    update['$set'] = set_embed

    try:
        container_info = mongo.db.container_info.find_one_and_update(
            query, update, return_document=True)
    except:
        return {"message": "galat menaikkan lvl pada container_info"}, 500

    return container_info


def forced_to_finish(activity, check_step):
    """
    Untuk cabang yang tidak memiliki gate out saat aktifitas bongkar delivery
    maka ketika di step 3 akan langsung mengupdate container info ke lvl 9 (finish)
    """
    return activity == "BONGKAR-DELIVERY" and check_step == "three"
