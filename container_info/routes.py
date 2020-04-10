from db import mongo

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
    get_jwt_claims,
)
from marshmallow import ValidationError
from bson.objectid import ObjectId

from container_info.container_info_schema import (
    ContainerInitSchema,
    ContainerEditInfoSchema
)

from datetime import datetime
import string


# Set up a Blueprint
bp = Blueprint('container_info_bp', __name__, url_prefix='/api')


"""
-------------------------------------------------------------------------------
CONTAINER LIST AND CREATE CONTAINER

document_level
1 info container init , 2 check one created, 3 check one finish
4 check two created, 5 check two finish
6 check three created, 7 check three finish
8 check four created, 9 check four finish document finish
-------------------------------------------------------------------------------
"""
@bp.route('/containers', methods=['GET', 'POST'])
@jwt_required
def get_container_list():

    claims = get_jwt_claims()

    if request.method == 'GET':

        """ 
        ?branch=SAMPIT    
        &  document_level=1 (lvl 1 s/d 9) 
        &  agent=MERATUS 
        & page=1
        &  search=""
        """

        branch = request.args.get("branch")
        document_level = request.args.get("document_level")
        agent = request.args.get("agent")
        search = request.args.get("search")

        # PAGGING
        page_number = 1
        page = request.args.get("page")
        LIMIT = 30
        if page:
            page_number = int(page)

        # find database
        find = {}

        if branch:
            find["branch"] = branch
        if document_level:
            # Jika dokumen lvl dimasukkan 0 maka untuk memunculkan doc lvl selain 5
            if document_level == "0":
                find["document_level"] = {'$ne': 9} #NOT EQUAL 9 karena 9 Dokumen Finish
            else:
                find["document_level"] = int(document_level)
        if agent:
            find["agent"] = agent
        if search:
            find["container_number"] = {'$regex': f'.*{search}.*'}

        container_coll = mongo.db.container_info.find(find).skip(
            (page_number - 1) * LIMIT).limit(LIMIT).sort("_id", -1)
        container_list = []

        for container in container_coll:
            container_list.append(container)

        return {"containers": container_list}, 200

    if request.method == 'POST':

        if not claims["isTally"]:
            return {"message": "user tidak memiliki hak akses untuk menambahkan data"}, 403

        schema = ContainerInitSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return err.messages, 400

        activity_list = ["RECEIVING-MUAT", "BONGKAR-DELIVERY"]
        if data["activity"].upper() not in activity_list:
            return {"message": "activity harus diantara RECEIVING-MUAT atau BONGKAR-DELIVERY"}, 400

        data_insert = {
            "container_number": data["container_number"].upper(),
            "voyage": data["voyage"].upper(),
            "size": data["size"],
            "tipe": data["tipe"].upper(),
            "full_or_empty": data["full_or_empty"].upper(),
            # "RECEIVING-MUAT  , BONGKAR-DELIVERY"
            "activity": data["activity"].upper(),
            "created_at": data["created_at"],
            "branch": data["branch"].upper(),

            # post client dari collection vessel
            "vessel_id": data["vessel_id"],
            "vessel": data["vessel"],
            # PENTING DIGUNAKAN UNTUK MEMUNCULKAN DI AGENT
            "agent":  data["agent"].upper(),

            # from data vessel
            "int_dom": data["int_dom"].upper(),

            # AUTO
            "creator_username": get_jwt_identity(),
            "creator_name": claims["name"],
            "updated_at": datetime.now(),
            "document_level": 1,
            "dammaged": False,
            "checkpoint": {
                "one": "",
                "two": "",
                "three": "",
                "four": ""
            },
            "checkpoint_status": {
                "one": "",
                "two": "",
                "three": "",
                "four": ""
            }
        }

        # DATABASE
        try:
            id = mongo.db.container_info.insert_one(data_insert).inserted_id
        except:
            return {"message": "galat insert container"}, 500

        return {"message": f"{id} data berhasil disimpan"}, 201


"""
-------------------------------------------------------------------------------
CONTAINER DETAIL, UBAH DAN HAPUS
-------------------------------------------------------------------------------
"""
@bp.route('/containers/<id_container>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required
def get_container_detail(id_container):

    claims = get_jwt_claims()
    if not ObjectId.is_valid(id_container):
        return {"message": "Object ID tidak valid"}, 400

    if request.method == 'GET':
        container = mongo.db.container_info.find_one(
            {'_id': ObjectId(id_container)})
        return jsonify(container), 200

    if request.method == 'PUT':

        """Melakukan update informasi pada info petikemas"""

        schema = ContainerEditInfoSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return err.messages, 400

        activity_list = ["RECEIVING-MUAT", "BONGKAR-DELIVERY"]
        if data["activity"].upper() not in activity_list:
            return {"message": "activity harus diantara RECEIVING-MUAT atau BONGKAR-DELIVERY"}, 400
        if not ObjectId.is_valid(id_container):
            return {"message": "Object ID tidak valid"}, 400
        if not claims["isTally"]:
            return {"message": "user ini tidak dapat melakukan edit dokumen"}, 403

        data_to_change = {
            "container_number": data["container_number"].upper(),
            "size": data["size"],
            "tipe": data["tipe"].upper(),
            "full_or_empty": data["full_or_empty"].upper(),
            "activity": data["activity"].upper(),
            "created_at": data["created_at"],

            "updated_at": datetime.now(),
            "creator_username": get_jwt_identity(),
            "creator_name": claims["name"]
        }

        # digunakan untuk memastikan tidak ada yang mengupdate sebelum update ini
        last_update = data["updated_at"]

        # Hanya document lvl 1 yang bisa diubah
        query = {'_id': ObjectId(id_container),
                 "updated_at": last_update,
                 "document_level": 1}
        update = {'$set': data_to_change}

        # MEMANGGIL DATABASE
        container = mongo.db.container_info.find_one_and_update(
            query, update, return_document=True)

        if container is None:
            return {"message": "Gagal update. Dokumen ini telah di ubah oleh seseorang sebelumnya. Harap cek data terbaru!"}, 402

        return jsonify(container), 201

    if request.method == 'DELETE':
        """
        DELETE HANYA DAPAT DILAKUKAN PADA DOKUMEN LVL 1 OLEH FOREMAN
        """
        if claims["isForeman"] or claims["isAdmin"]:
            query = {'_id': ObjectId(id_container),
                     'branch': claims["branch"][0],
                     'document_level': 1}
            container = mongo.db.container_info.find_one_and_delete(query)
            if container is None:
                return {"message": "Dokumen yang sudah dilakukan pengecekan tidak dapat dihapus"}, 406
            return {"message": "Dokumen berhasil di hapus"}, 204

        return {"message": "Dokumen hanya bisa di hapus oleh Manajer atau Foreman"}, 403
