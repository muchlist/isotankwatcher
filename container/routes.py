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

from container.container_schema import (
    ContainerInitSchema,
    ContainerEditInfoSchema,
    ContainerLvlUpSchema,
    CheckContainerSchema
)

from datetime import datetime
import string
import random


# Set up a Blueprint
bp = Blueprint('container_bp', __name__)

# ID generator untuk status Array agar gampang di manipulasi


def id_generator(size=4, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


@bp.route('/containers', methods=['GET', 'POST'])
@jwt_required
def get_container_list():

    claims = get_jwt_claims()

    if request.method == 'GET':

        """ ?branch=SAMPIT    
        &  document_level=1 (spesial case 23) 
        &  agent=MERATUS & page=1"""

        branch = request.args.get("branch")
        document_level = request.args.get("document_level")
        agent = request.args.get("agent")

        # PAGGING
        page_number = 1
        page = request.args.get("page")
        LIMIT = 40
        if page:
            page_number = int(page)

        find = {}

        if branch:
            find["branch"] = branch
        if document_level:
            # untuk memunculkan lvl2 dan lvl3
            if document_level == "23":
                find["document_level"] = {'$in': [2, 3]}
            else:
                find["document_level"] = int(document_level)
        if agent:
            find["agent"] = agent

        container_coll = mongo.db.container.find(find).skip(
            (page_number - 1) * LIMIT).limit(LIMIT).sort("_id", -1)
        container_list = []

        for container in container_coll:
            container_list.append(container)

        return {"containers": container_list}, 200

    if request.method == 'POST':

        """
        INIT DATA TIDAK BISA DILAKUKAN OLEH AGENT, Hanya bisa dilakukan oleh
        tally, foreman, admin
        INIT DATA DAPAT DILAKUKAN DENGAN MEMUAT STATUS PERTAMA, ATAU BLANK STATUS
        DENGAN MENGGUNAKAN QUERY ?blank=true
        """

        if claims["isTally"] or claims["isForeman"] or claims["isAdmin"]:

            schema = ContainerInitSchema()
            try:
                data = schema.load(request.get_json())
            except ValidationError as err:
                return err.messages, 400

            # document_level = 1.Progress , 2.Ready, 3.Selesai
            data_insert = {
                "job_number": data["job_number"],
                "container_number": data["container_number"].upper(),
                "voyage": data["voyage"].upper(),
                "size": data["size"],
                "tipe": data["tipe"].upper(),
                "full_or_empty": data["full_or_empty"].upper(),
                "activity": data["activity"].upper(),
                "created_at": data["created_at"],

                # post client dari collection vessel
                "vessel_id": data["vessel_id"],
                "vessel": data["vessel"],
                # PENTING DIGUNAKAN UNTUK MEMUNCULKAN DI AGENT
                "agent":  data["agent"].upper(),


                # AUTO FROM CLIENT
                # search client dari jwt user
                "branch": data["branch"].upper(),

                # from data vessel
                "int_dom": data["int_dom"].upper(),

                # AUTO
                "approval_foreman": False,
                "approval_foreman_name": "",
                "approval_agent": False,
                "approval_agent_name": "",
                "creator_username": get_jwt_identity(),
                "creator_name": claims["name"],
                "updated_at": datetime.now(),
                "url_img_up": "",
                "url_img_bottom": "",
                "url_img_front": "",
                "url_img_back": "",
                "url_img_left": "",
                "url_img_right": "",
                "document_level": 1
            }

            if request.args.get("blank"):
                # jika blank data insert dimasukkan status kosong
                data_insert["status"] = []
                data_insert["last_status"] = "INIT"
            else:
                # JIKA TIDAK BLANK
                status_insert = {
                    "status_id": id_generator(),
                    "checked_at": data["checked_at"],
                    "check_position": data["check_position"],
                    "status": data["status"].upper(),
                    "witness": data["witness"].upper(),
                    "witness_img_url": data["witness_img_url"],
                    "note": data["note"],

                    # AUTO
                    "checked_by": get_jwt_identity(),
                    "checked_by_name": claims["name"],
                }

                # jika tidak blank data insert dimasukkan status
                data_insert["status"] = [status_insert]
                data_insert["last_status"] = data["status"].upper()

            try:
                mongo.db.container.insert_one(data_insert)
            except:
                return {"message": "galat insert container"}, 500

            return {"message": "data berhasil disimpan"}, 201

        return {"message": "user tidak memiliki hak akses untuk menambahkan data"}, 401


@bp.route('/containers/<id_container>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required
def get_container_detail(id_container):

    claims = get_jwt_claims()

    if request.method == 'GET':
        if not ObjectId.is_valid(id_container):
            return {"message": "Object ID tidak valid"}, 400

        container = mongo.db.container.find_one(
            {'_id': ObjectId(id_container)})
        return jsonify(container), 200

    if request.method == 'PUT':

        """Melakukan update informasi pada petikemas selain status"""

        schema = ContainerEditInfoSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return err.messages, 400

        if not ObjectId.is_valid(id_container):
            return {"message": "Object ID tidak valid"}, 400

        if claims["isTally"] or claims["isForeman"] or claims["isAdmin"]:

            data_to_change = {
                "container_number": data["container_number"].upper(),
                "vessel_id": data["vessel_id"],
                "vessel": data["vessel"].upper(),
                "voyage": data["voyage"].upper(),
                "size": data["size"],
                "tipe": data["tipe"].upper(),
                "full_or_empty": data["full_or_empty"].upper(),
                "activity": data["activity"].upper(),
                "int_dom": data["int_dom"].upper(),
                "created_at": data["created_at"],

                "updated_at": datetime.now(),
                "creator_username": get_jwt_identity(),
                "creator_name": claims["name"]
            }

            # digunakan untuk memastikan tidak ada yang mengupdate sebelum update ini
            last_update = data["updated_at"]

            query = {'_id': ObjectId(id_container),
                     "updated_at": last_update,
                     "document_level": 1}
            update = {'$set': data_to_change}

            # MEMANGGIL DATABASE
            container = mongo.db.container.find_one_and_update(
                query, update, return_document=True)

            if container is None:
                return {"message": "Gagal update. Dokumen ini telah di ubah oleh seseorang sebelumnya. Harap cek data terbaru!"}, 302

            return jsonify(container), 201

        return {"message": "user ini tidak dapat melakukan edit dokumen"}, 401

    if request.method == 'DELETE':

        """
        DELETE HANYA DAPAT DILAKUKAN PADA DOKUMEN LVL 1 OLEH FOREMAN
        """

        if claims["isForeman"] or claims["isAdmin"]:

            container = mongo.db.container.find_one(
                {'_id': ObjectId(id_container)}, {"document_level": 1})

            # Hanya dokumen level 1 yang bisa di delete
            if container["document_level"] == 1:
                mongo.db.container.delete_one({'_id': ObjectId(id_container)})
                return {"message": "Dokumen berhasil di hapus"}, 204

            return {"message": "Dokumen berstatus siap tidak dapat dihapus"}, 403

        return {"message": "Dokumen hanya bisa di hapus oleh Manajer atau Foreman"}, 401


"""Hanya dapat dilakukan tally dan foreman apabila lvl doc 1"""
@bp.route('/containers/<id_container>/ready', methods=['POST'])
@jwt_required
def change_lvl_from_1_to_2(id_container):

    claims = get_jwt_claims()

    if claims["isTally"] or claims["isForeman"]:

        schema = ContainerLvlUpSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return err.messages, 400

        if not ObjectId.is_valid(id_container):
            return {"message": "Object ID tidak valid"}, 400

        query = {
            '_id': ObjectId(id_container),
            "updated_at": data["updated_at"],
            "document_level": 1
        }
        update = {
            '$set': {"document_level": 2}
        }

        # DATABASE
        container = mongo.db.container.find_one_and_update(
            query, update, return_document=True
        )

        if container is None:
            return {"message": "Gagal update. Dokumen ini telah di ubah oleh seseorang sebelumnya. Harap cek data terbaru!"}, 302

        return jsonify(container), 201

    return {"message": "User tidak memiliki hak akses untuk merubah dokumen ini"}, 403


"""Hanya dapat dilakukan tally dan foreman apabila lvl doc 2"""
@bp.route('/containers/<id_container>/unready', methods=['POST'])
@jwt_required
def change_lvl_form_2_to_1(id_container):

    claims = get_jwt_claims()

    if claims["isTally"] or claims["isForeman"]:

        schema = ContainerLvlUpSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return err.messages, 400

        query = {
            '_id': ObjectId(id_container),
            "updated_at": data["updated_at"],
            "document_level": 2
        }
        update = {
            '$set': {"document_level": 1}
        }

        # DATABASE
        container = mongo.db.container.find_one_and_update(
            query, update, return_document=True
        )

        if container is None:
            return {"message": "Gagal update. Dokumen ini telah di ubah oleh seseorang sebelumnya. Harap cek data terbaru!"}, 302

        return jsonify(container), 201

    return {"message": "User tidak memiliki hak akses untuk merubah dokumen ini"}, 403


"""Hanya dapat dilakukan foreman mengembalikan dokumen approve ke editable karena keadaan tertentu"""
@bp.route('/containers/<id_container>/unapprove', methods=['POST'])
@jwt_required
def change_lvl_form_3_to_1(id_container):
    claims = get_jwt_claims()

    if claims["isForeman"]:

        schema = ContainerLvlUpSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return err.messages, 400

        if not ObjectId.is_valid(id_container):
            return {"message": "Object ID tidak valid"}, 400

        query = {
            '_id': ObjectId(id_container),
            "updated_at": data["updated_at"],
            "document_level": 3
        }
        update = {
            '$set': {
                "document_level": 1,
                "updated_at": datetime.now(),
                "approval_foreman": False,
                "approval_foreman_name": f"Dibatalkan - {claims['name']}"
            }
        }

        # DATABASE
        container = mongo.db.container.find_one_and_update(
            query, update, return_document=True
        )

        if container is None:
            return {"message": "Gagal update. Dokumen ini telah di ubah oleh seseorang sebelumnya. Harap cek data terbaru!"}, 302

        return jsonify(container), 201

    return {"message": "User tidak memiliki hak akses untuk merubah dokumen ini"}, 403


"""
approval digunakan bisa oleh foreman atau oleh agent dengan syarat dokumen harus 
ber lvl 2 ke 3 untuk foreman
ber lvl 3 ke 4 untuk agent
"""
@bp.route('/containers/<id_container>/approval', methods=['POST'])
@jwt_required
def approval(id_container):

    schema = ContainerLvlUpSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return err.messages, 400

    if not ObjectId.is_valid(id_container):
        return {"message": "Object ID tidak valid"}, 400

    claims = get_jwt_claims()

    # JIKA foreman harus lvl 2 ke lvl 3
    # JIKA Agent harus lvl 3 ke lvl 4
    if claims["isForeman"]:

        query = {
            '_id': ObjectId(id_container),
            "updated_at": data["updated_at"],
            "document_level": 2
        }
        update = {
            '$set': {
                "document_level": 3,
                "approval_foreman": True,
                "approval_foreman_name": claims["name"],
                "updated_at": datetime.now()
            }
        }

        # DATABASE
        container = mongo.db.container.find_one_and_update(
            query, update, return_document=True
        )

        if container is None:
            return {"message": "Gagal update. Dokumen ini telah di ubah oleh seseorang sebelumnya. Harap cek data terbaru!"}, 302

        return jsonify(container), 201

    elif claims["isAgent"]:

        query = {
            '_id': ObjectId(id_container),
            "updated_at": data["updated_at"],
            "document_level": 3,
            "agent": claims["company"]
        }
        update = {
            '$set': {
                "document_level": 4,
                "approval_agent": True,
                "approval_agent_name": claims["name"],
                "updated_at": datetime.now()
            }
        }

        # DATABASE
        container = mongo.db.container.find_one_and_update(
            query, update, return_document=True
        )

        if container is None:
            return {"message": "Gagal update. Dokumen belum disetujui pihak Pelindo atau Dokumen berbeda Perusahaan."}, 302

        return jsonify(container), 201
    else:
        return {"message": "user tidak memiliki hak akses untuk mengedit dokumen"}, 403


@bp.route('/containers/<id_container>/status', methods=['POST'])
@jwt_required
def add_status(id_container):

    if request.method == 'POST':
        schema = CheckContainerSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return err.messages, 400

        if not ObjectId.is_valid(id_container):
            return {"message": "Object ID tidak valid"}, 400

        claims = get_jwt_claims()

        if claims["isForeman"] or claims["isTally"]:

            find = {
                '_id': ObjectId(id_container),
                "document_level": 1
            }

            status_insert = {
                "status_id": id_generator(),
                "checked_at": data["checked_at"],
                "check_position": data["check_position"],
                "status": data["status"].upper(),
                "witness": data["witness"].upper(),
                "witness_img_url": data["witness_img_url"],
                "note": data["note"],

                # AUTO
                "checked_by": get_jwt_identity(),
                "checked_by_name": claims["name"],
            }

            # DATABASE
            container = mongo.db.container.find_one_and_update(
                find,
                {'$set': {"updated_at": datetime.now()}, '$push': {
                    'status': status_insert}},
                return_document=True
            )
            if container is None:
                return {"message": "Gagal update. Dokumen ini telah di ubah oleh seseorang sebelumnya. Harap cek data terbaru!"}, 302
            return jsonify(container), 201
        return {"message": "User ini tidak memiliki hak akses untuk menambahkan status"}, 403


@bp.route('/containers/<id_container>/status/<id_status>', methods=['DELETE'])
@jwt_required
def remove_status(id_container, id_status):

    if not ObjectId.is_valid(id_container):
        return {"message": "Object ID tidak valid"}, 400

    claims = get_jwt_claims()
    if claims["isForeman"] or claims["isTally"]:
        find = {
            '_id': ObjectId(id_container),
            "document_level": 1
        }

        # DATABASE
        container = mongo.db.container.find_one_and_update(
            find,
            {'$set': {"updated_at": datetime.now()}, '$pull': {'status': {
                'status_id': id_status}}},
            return_document=True
        )
        if container is None:
            return {"message": "Gagal update. Dokumen ini telah di ubah oleh seseorang sebelumnya. Harap cek data terbaru!"}, 302
        return jsonify(container), 201
    return {"message": "User ini tidak memiliki hak akses untuk menambahkan status"}, 403
