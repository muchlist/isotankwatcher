from marshmallow import Schema, fields


class CheckContainerSchema(Schema):
    #checked_by = fields.Str(required=True)
    #checked_by_name = fields.Str(required=True)
    checked_at = fields.DateTime(required=True)
    check_position = fields.Str(required=True)
    status = fields.Str(required=True)  # list di form mas tri
    note = fields.Str(required=True)  # list di form mas tri
    witness = fields.Str(required=True)


class ContainerInitSchema(Schema):
    job_number = fields.Str(required=True)
    container_number = fields.Str(required=True)
    vessel_id = fields.Str(required=True)
    vessel = fields.Str(required=True)
    voyage = fields.Str(required=True)
    agent = fields.Str(required=True)
    branch = fields.Str(required=True)
    #status = fields.List(fields.Nested(CheckContainerSchema, required=False))

    checked_at = fields.DateTime(required=False)
    check_position = fields.Str(required=False)
    status = fields.Str(required=False)  # list di form mas tri
    witness = fields.Str(required=False)
    note = fields.Str(required=False)
    # checked_by = fields.Str(required=True)
    # checked_by_name = fields.Str(required=True)

    size = fields.Int(required=True)  # 20 40 45 Feet
    tipe = fields.Str(required=True)  # Dry Rfr Tnk Flt o/d
    full_or_empty = fields.Str(required=True)
    activity = fields.Str(required=True)
    int_dom = fields.Str(required=True)
    # doc_level: 1
    # last_status = fields.Str(required=True)
    # approval_foreman = fields.Bool(required=True)
    # approval_agent = fields.Bool(required=True)
    # creator_username = fields.Str(required=True)
    # creator_name = fields.Str(required=True)
    # created_at = fields.DateTime(required=False)
    # updated_at = fields.DateTime(required=False)   otomatis
    # name = fields.Str(required=True) otomati
    # cabang = fields.Str(required=True) otomatis
    # url_img 0-5
    # file_photo

class ContainerEditInfoSchema(Schema):

    container_number = fields.Str(required=True)
    vessel_id = fields.Str(required=True)
    vessel = fields.Str(required=True)
    voyage = fields.Str(required=True)
    agent = fields.Str(required=True)
    size = fields.Int(required=True)  # 20 40 45 Feet
    tipe = fields.Str(required=True)  # Dry Rfr Tnk Flt o/d
    full_or_empty = fields.Str(required=True)
    activity = fields.Str(required=True)
    int_dom = fields.Str(required=True)

    updated_at = fields.DateTime(required=True)
    # creator_username = fields.Str(required=True)
    # creator_name = fields.Str(required=True)

class ContainerLvlUpSchema(Schema):
    updated_at = fields.DateTime(required=True)