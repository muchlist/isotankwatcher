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
    ContainerCheckPassSchema
)
import utils.generate_qrcode as qr

from datetime import datetime

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
        '$set': {
            f"checkpoint.{step.lower()}": f"{container_id}-{step.lower()}",
            f"checkpoint_status.{step.lower()}": f'{data["status"]} : {data["note"]}',
            'updated_at': datetime.now()
        },
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
        "witness_note": "",
        "witness_approved": False
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
        "nopol": data["nopol"],
        "image":  image_embed,
        "approval": approval_data_embed,
        "doc_level": 1, # 1 init , 2 approve by tally, 3 approve by manager or foreman
    }

    # DATABASE container check BEGIN
    try:
        mongo.db.container_check.insert_one(data_insert)
    except:
        return {"message": "galat insert container_check, kemungkinan data sudah ada"}, 500
    # DATABASE container check END

    # CREATE QR CODE
    create_qr_code(f"{container_id}-{step}")

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
                "nopol": data["nopol"],
                'approval.witness': data["witness"],
                'updated_at': datetime.now()
            }
        }
        try:
            # Update container check
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


"""
-------------------------------------------------------------------------------
PASS Check Container Position
permintaan tambahan dari pak gm sehingga harus merubah urutan step karena
ternyata ada step yang sifatnya optional,
ini menjadi tambalan kode yang seharusnya merubah struktur sebelumnya
-------------------------------------------------------------------------------
"""
@bp.route('/pass-check/<container_id>/<step>/<activity>', methods=['POST'])
@jwt_required
def pass_check_container(container_id, step, activity):

    claims = get_jwt_claims()

    if not ObjectId.is_valid(container_id):
        return {"message": "Object ID tidak valid"}, 400

    if not step in ("one", "two", "three", "four"):
        return {"message": "step harus diantara one, two, three, four"}, 400

    if not activity in ("RECEIVING-MUAT", "BONGKAR-DELIVERY"):
        return {"message": "activity harus diantara RECEIVING-MUAT, BONGKAR-DELIVERY"}, 400

    schema = ContainerCheckPassSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return err.messages, 400
        

    if not claims["isTally"]:
        return {"message": "user tidak memiliki hak akses untuk merubah data"}, 403

    # DATABASE CONTAINER_INFO BEGIN
    if activity == "RECEIVING-MUAT":
        switch = {
            "one": [1, 2], # 1 document created, 2 check one created
            "two": [3, 4],  # 3 check one finish, 4 check two created
            "three": [5, 6],  # 5 check two finish, 6 check three created,
            "four": [7, 8],  # 7 check three finish, 8 check four created,
        }
    else:
        switch = {
            # PADA Aktifitas BONGKAR DELIVERY TIDAK DIIJINKAN PASS step three
            # di buat angka salah (0) sehingga pada querry dia akan gagal ditemukan
            "one": [1, 2], # 1 document created, 2 check one created
            "two": [3, 4],  # 3 check one finish, 4 check two created
            "three": [5, 6],  # 5 check two finish, 6 check three created,
        }
    # db.inventory.find ( { quantity: { $in: [20, 50] } } ) <- example
    query = {
        '_id': ObjectId(container_id),
        'document_level': {'$in': switch.get(step)},
        'activity': activity,
        'updated_at': data["updated_at"]
    }

    # Jika dokumen yang dipass step two maka document lvl akan lompat ke 5
    # Jika dokumen yang dipass step two maka document lvl akan lompat ke 7
    if step == "one":
        document_level_update = 3
    elif step == "two":
        document_level_update = 5
    elif step == "three":
        # JIKA RECEIVING MUAT PASS AKAN KE LVL 7, NAMUN BONGKAR DELIVERY AKAN 
        # KE LVL 9 KARENA RIDAK ADA GATEOUT
        if activity == "RECEIVING-MUAT":
            document_level_update = 7
        else:
            document_level_update = 9
    else:
        document_level_update = 9

    update = {
        # Memasukkan ID check dan Status dan Note Pengecekan ke Container Info
        '$set': {
            f"checkpoint.{step.lower()}": "PASS",
            f"checkpoint_status.{step.lower()}": "PASS",
            "document_level": document_level_update,
            'updated_at': datetime.now()
        },

    }
    try:
        container_info = mongo.db.container_info.find_one_and_update(
            query, update, return_document=True)
    except:
        return {"message": "galat insert pada container_info"}, 500

    if container_info is None:
        return {"message": "PASS Document tidak memenuhi syarat, atau data update terakhir salah"}, 400
    # DATABASE CONTAINER_INFO END

    # DATABASE container check BEGIN
    try:
        mongo.db.container_check.remove({'_id': f"{container_id}-{step}"})
    except:
        return {"message": "galat delete pada container_check"}, 500
    # DATABASE container check END

    return jsonify(container_info), 200


"""
-------------------------------------------------------------------------------
Menyalin gambar dari container check sebelumnya
-------------------------------------------------------------------------------
"""
@bp.route('/copy-photo-to/<container_check_id>', methods=['GET'])
@jwt_required
def copy_photo_check_container(container_check_id):
    claims = get_jwt_claims()
    stepdata = get_step_from_container_check_id(container_check_id)
    check_id_without_step = stepdata[0]
    step = stepdata[1]

    if step == "one":
        return {"message": "tidak dapat melakukan copy image pada step one"}, 400

    if not claims["isTally"]:
        return {"message": "user tidak memiliki hak akses untuk menambahkan data"}, 403

    step_list = ["one", "two", "three", "four"]
    step_map = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4
    }

    container_check_data = None
    for x in range(step_map.get(step)-1, 0, -1):
        container_check_id_before = f"{check_id_without_step}-{step_list[x - 1]}"
        container_check_data = mongo.db.container_check.find_one(
            {'_id': container_check_id_before})
        if container_check_data is not None:
            break

    query = {
        '_id': container_check_id,
        'doc_level': 1
    }
    update = {
        '$set': {
            'image.url_img_back': container_check_data["image"]["url_img_back"],
            'image.url_img_bottom': container_check_data["image"]["url_img_bottom"],
            'image.url_img_front': container_check_data["image"]["url_img_front"],
            'image.url_img_left': container_check_data["image"]["url_img_left"],
            'image.url_img_right': container_check_data["image"]["url_img_right"],
            'image.url_img_up': container_check_data["image"]["url_img_up"],
        }
    }
    container_check_data = mongo.db.container_check.find_one_and_update(
        query, update, return_document=True)
    if container_check_data is None:
        return {"message": "Tidak dapat melakukan update image saat document sudah ready"}, 400

    return jsonify(container_check_data), 200


def get_step_from_container_check_id(container_check_id):
    # index 0 = container id
    # index 1 = container step
    splitted = container_check_id.split("-")
    return splitted


def translate_step(activity, step):
    receiving_muat = {"one": "GATE IN",
                      "two": "CY-STACK",
                      "three": "CY-UNSTACK (Muat)",
                      "four": "DERMAGA"}
    bongkar_delivery = {"one": "DERMAGA",
                        "two": "CY-STACK",
                        "three": "CY-UNSTACK (Delivery)",
                        "four": "GATE OUT"}
    if activity == "RECEIVING-MUAT":
        return receiving_muat.get(step.lower())
    elif activity == "BONGKAR-DELIVERY":
        return bongkar_delivery.get(step.lower())
    else:
        return None


def create_qr_code(container_check_id):
    # MEMBUAT QRCODE Untuk setiap container check
    try:
        qr.generate_qr(container_check_id)  # qr/container_check_id.png
    except:
        return {"message": "document berhasil dibuat, namun qrcode gagal"}, 302
