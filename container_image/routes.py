from db import mongo

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
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
bp = Blueprint('container_image_bp', __name__, url_prefix='/api')


@bp.route('/upload/image/<container_check_id>/<position>', methods=['POST'])
@jwt_required
def upload_image(container_check_id, position):
    # static/images/namafolder/namafile
    schema = ImageSchema()
    try:
        data = schema.load(request.files)
    except ValidationError as err:
        return err.messages, 400

    # Cek path posisi gambar, selain witness
    if position not in ["up", "bottom", "front", "back", "left", "right", "witness"]:
        return {"message": "path salah"}, 400

    # AUTH
    claims = get_jwt_claims()
    if not (claims['isTally'] or claims['isForeman']):
        return {"message": "user ini tidak memiliki hak akses untuk mengupload"}, 403

    # Cek extensi untuk nama file custom
    extension = image_helper.get_extension(data['image'])
    # Nama file dan ekstensi
    fileName = f"{container_check_id}-{position}{extension}"
    today = datetime.now()
    folder = str(today.year)+"B"+str(today.month)

    # SAVE IMAGE
    try:
        image_path = image_helper.save_image(
            data['image'], folder=folder, name=fileName)
        basename = image_helper.get_basename(image_path)

        # DATABASE
        # key di database berdasarkan posisi gambar path url
        key = f"image.url_img_{position}"
        container = mongo.db.container_check.find_one_and_update(
            {'_id': container_check_id},
            {'$set': {key: image_path}}, {'_id': 1}
        )

        if container is None:
            return {"message": "container check id salah"}, 400
            
        return {"message": f"image {image_path} uploaded"}, 201

    except UploadNotAllowed:
        extension = image_helper.get_extension(data['image'])
        return {"message": f"extensi {extension} not allowed"}, 406
