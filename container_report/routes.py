from db import mongo


from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
    get_jwt_claims,
)
from marshmallow import ValidationError

from container_report.container_report_schema import (
    ContainerReportSchema
)
from utils.pdf import generate_report_pdf as grp

from datetime import datetime
import random
import string
import time

# Set up a Blueprint
bp = Blueprint('container_report_bp', __name__, url_prefix='/api')


"""
-------------------------------------------------------------------------------
Container Check list, GET
memproses check lvl 3 (yang sudah diapprove oleh foreman)
by date range
mengembalikan nama pdf yang di generate
-------------------------------------------------------------------------------
"""
@bp.route('/container-check-reports', methods=['POST'])
@jwt_required
def reports_check_container_list():
    # claims = get_jwt_claims()
    schema = ContainerReportSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return err.messages, 400

    branch = data["branch"].strip().upper()
    start_date = data["start_date"]
    end_date = data["end_date"]

    # find database
    find_opt = {
        "doc_level": 3,
        "container.branch": branch,
        "checked_at": {
            '$gte': start_date,
            '$lt': end_date,
            # '$gte' : datetime(2019,1,1),
            # '$lt' : datetime(2020,5,5),
        }
    }

    container_check_coll = mongo.db.container_check.find(
        find_opt).sort("checked_at", 1)
    # container_check_coll = mongo.db.container_check.find(
    #     find_opt).sort("checked_at", 1)

    container_check_list = []

    for container_check in container_check_coll:
        container_check_list.append(container_check)

    if len(container_check_list) == 0:
        return {"message": "data tidak ditemukan"}, 404

    pdf_file_name = create_random_name()

    # MEMBUAT PDF START
    try:
        grp.generate_pdf(pdf_file_name, container_check_list, start_date, end_date)
    except:
        return {"message": "Gagal membuat pdf!"}, 403
    # MEMBUAT PDF END

    return {"message": pdf_file_name}, 200


def create_random_name():
    time_epoch = str(int(time.time()))
    random_string_name = random_string(5)
    return f'{time_epoch}-{random_string_name}.pdf'


def random_string(stringLength):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

