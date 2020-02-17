from db import mongo

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
    get_jwt_claims,
)
from marshmallow import ValidationError
from bson.objectid import ObjectId
from flask_uploads import UploadNotAllowed

from utils import image_helper
from container_image.image_schema import ImageSchema

from datetime import datetime
import string
import random

# Set up a Blueprint
bp = Blueprint('container_image_bp', __name__)


def id_generator(size=5, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

"""
Memerlukan pemisahan knowledge antara foto container dan foto witness
pada foto container hasil upload otomatis dimasukkan pathnya ke database
sedangkan foto saksi(witness) berbeda karena fotonya harus ada lebih dulu sebelum
statusnya ditambahkan, sehingga disederhanakan menjadi foto diupload dan url
dikembalikan sebagai response untuk dimasukkan lagi ke status container
"""

@bp.route('/upload/image/<container_id>/<position>', methods=['POST'])
@jwt_required
def upload_image(container_id, position):
    #static/images/namafolder/namafile
    schema = ImageSchema()
    try:
        data = schema.load(request.files)
    except ValidationError as err:
        return err.messages, 400

    if not ObjectId.is_valid(container_id):
        return {"message": "Object ID tidak valid"}, 400

    #Cek path posisi gambar, selain witness
    if position not in ["up", "bottom", "front", "back", "left", "right", "witness"]:
        return {"message": "path salah"}, 400

    # AUTH
    claims = get_jwt_claims()
    if claims['isTally'] or claims['isForeman']:

        # Cek extensi untuk nama file custom
        extension = image_helper.get_extension(data['image'])
        # Nama file dan ekstensi
        fileName = f"{container_id}-{id_generator()}{extension}"
        today = datetime.now()
        folder = str(today.year)+"B"+str(today.month)

        #SAVE IMAGE
        try:
            image_path = image_helper.save_image(
                data['image'], folder=folder, name=fileName)
            basename = image_helper.get_basename(image_path)

            # DATABASE
            # key di database berdasarkan posisi gambar path url
            if position != "witness":
                """jika posisi == witness, tidak melakukan penyimpanan url di
                database, hanya menyimpan foto dan mengembalikan url"""

                key = f"url_img_{position}"
                container = mongo.db.container.find_one_and_update(
                    {'_id': ObjectId(container_id)},
                    {'$set': {key: image_path}}, {'_id': 1}
                )

                if container is None:
                    return {"message": "container id salah"},400

            return {"message": f"image {image_path} uploaded"}, 201

        except UploadNotAllowed:
            extension = image_helper.get_extension(data['image'])
            return {"message": f"extensi {extension} not allowed"}, 406

    return {"message": "user ini tidak memiliki hak akses untuk mengupload"}, 403
