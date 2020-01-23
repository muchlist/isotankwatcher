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
from container.container_schema import ContainerInitSchema

from datetime import datetime


# Set up a Blueprint
bp = Blueprint('container_bp', __name__)


@bp.route('/containers', methods=['GET','POST'])
@jwt_required
def get_container_list():
    if request.method == 'GET':
        container_coll = mongo.db.container.find({})
        container_list = []
        for container in mongo_result:
            container_list.append(container)
        
        return {"containers": container_list}, 200
        
    
    if request.method == 'POST':

        schema = ContainerInitSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return err.messages, 400

        # check_time = datetime.now()
        # print("ini cuuk")
        # print(check_time)

        data_insert = {
            "username": data["username"],
            "position": data["position"],
            "check_time": data["check_time"]
        }
        try:
            mongo.db.container.insert_one(data_insert)
        except:
            return {"message": "galat insert register"}, 500

        return {"message": "data berhasil disimpan"}, 201