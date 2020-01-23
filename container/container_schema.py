from marshmallow import Schema, fields


class CheckContainerSchema(Schema):
    checked_by = fields.Str(required=True)
    checked_at = fields.DateTime(required=True)
    position = fields.Str(required=True)
    status = fields.Str(required=True)  # list di form mas tri
    witness = fields.Str(required=True)


class ContainerInitSchema(Schema):
    job_number = fields.Str(required=True)
    container_number = fields.Str(required=True)
    status = fields.List(fields.Nested(CheckContainerSchema, required=False))
    last_status = fields.Str(required=True)  # gatein gateout
    size = fields.Int(required=True)  # 20 40 45 Feet
    tipe = fields.Str(required=True)  # Dry Rfr Tnk Flt o/d
    full_or_empty = fields.Str(required=True)
    vessel_id = fields.Str(required=True)
    vessel = fields.Str(required=True)
    voyage = fields.Str(required=True)
    approval_foreman = fields.Bool(required=True)
    approval_agent = fields.Bool(required=True)
    creator_username = fields.Str(required=True)
    created_at = fields.DateTime(required=False)
    # diupdate = fields.DateTime(required=False)   otomatis
    # nama_user = fields.Str(required=True) otomati
    # cabang = fields.Str(required=True) otomatis
    # url_img 0-5
    # file_photo
