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
from vessel.vessel_schema import VesselRegisterSchema
from bson.objectid import ObjectId


# Set up a Blueprint
bp = Blueprint('vessel_bp', __name__)


@bp.route('/vessels', methods=['GET', 'POST'])  # ?search=
@jwt_required
def get_vessel_list():

    claims = get_jwt_claims()

    if request.method == 'GET':

        search = request.args.get("search")
        if search:
            query_string = {'$regex': f'.*{search}.*'}
            vessel_collection = mongo.db.vessel.find(
                {"ship_name": query_string})
        else:
            vessel_collection = mongo.db.vessel.find()

        vessels_list = []
        for vessel in vessel_collection:
            vessels_list.append(vessel)

        return {"vessels": vessels_list}, 200

    if request.method == 'POST':
        schema = VesselRegisterSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return err.messages, 400

        if claims["isForeman"] or claims["isTally"]:

            if "isActive" not in data:
                data["isActive"] = True

            data_insert = {
                "ship_name": data["ship_name"].upper(),
                "agent": data["agent"].upper(),
                "isInternational": data["isInternational"],
                "isActive": data["isActive"]
            }
            try:
                mongo.db.vessel.insert_one(data_insert)
            except:
                return {"message": "galat insert register"}, 500

            return {"message": "data berhasil disimpan"}, 201
            
        return {"message": "User ini tidak memiliki hak akses untuk menambahkan status"}, 403


@bp.route('/vessels/<vessel_id>', methods=['GET', 'POST'])
@jwt_required
def get_vessel_detail(vessel_id):

    isAdmin = get_jwt_claims()["isAdmin"]
    if not ObjectId.is_valid(vessel_id):
        return {"message": "Object Id tidak valid"}, 400

    if request.method == 'GET':
        ship = mongo.db.vessel.find_one({'_id': ObjectId(vessel_id)})
        return jsonify(ship), 200

    if request.method == 'POST':
        if not isAdmin:
            return {"message": "Hanya dapat diubah oleh admin"}, 403

        schema = VesselRegisterSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return err.messages, 400

        data_to_change = {
            "ship_name": data["ship_name"].upper(),
            "agent": data["agent"].upper(),
            "isInternational": data["isInternational"],
            "isActive": data["isActive"]
        }

        try:
            mongo.db.vessel.update_one({'_id': ObjectId(vessel_id)}, {
                                       '$set': data_to_change})
        except:
            return {"message": "galat, database gagal diakses"}, 500

        data_to_change["_id"] = vessel_id

        return jsonify(data_to_change), 200
