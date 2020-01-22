from marshmallow import Schema, fields

# Untuk load dari json saja , untuk dump langsung filter di mongodb + jsonify


class CheckContainerSchema(Schema):
    dicek_oleh = fields.Str(required=True)
    waktu_cek = fields.DateTime(required=True)
    status = fields.Str(required=True)  # list di form mas tri
    saksi = fields.Str(required=True)


class ContainerInputSchema(Schema):
    # nama_user = fields.Str(required=True) otomati
    # cabang = fields.Str(required=True) otomatis
    dibuat = fields.DateTime(required=False)
    # diupdate = fields.DateTime(required=False)   otomatis
    gate_in_status = fields.Nested(CheckContainerSchema, required=False)
    gate_out_status = fields.Nested(CheckContainerSchema, required=False)
    bongkar_status = fields.Nested(CheckContainerSchema, required=False)
    muat_status = fields.Nested(CheckContainerSchema, required=False)
    status_terakhir = fields.Str(required=True)  # gatein gateout
    ukuran_container = fields.Int(required=True)  # 20 40 45 Feet
    tipe_container = fields.Str(required=True)  # Dry Rfr Tnk Flt o/d
    full_or_empty = fields.Str(required=True)
    vessel = fields.Str(required=True)
    voyage = fields.Str(required=True)
    approval_foreman = fields.Bool(required=True)
    approval_agent = fields.Bool(required=True)
    # url_img 0-5
    # file_photo 
