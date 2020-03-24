from marshmallow import Schema, fields


class ContainerInitSchema(Schema):
    container_number = fields.Str(required=True)
 
    created_at = fields.DateTime(required=True)
    size = fields.Int(required=True)  # 20 40 45 Feet
    tipe = fields.Str(required=True)  # Dry Rfr Tnk Flt o/d
    full_or_empty = fields.Str(required=True)
    activity = fields.Str(required=True)
    
    int_dom = fields.Str(required=True)
    vessel_id = fields.Str(required=True)
    vessel = fields.Str(required=True)
    voyage = fields.Str(required=True)
    agent = fields.Str(required=True)
    branch = fields.Str(required=True)

    #branch
    #creator_name
    #creator_user_name
    #document_level
    #updated_at

class ContainerEditInfoSchema(Schema):
    container_number = fields.Str(required=True)
    created_at = fields.DateTime(required=True)
    size = fields.Int(required=True)  # 20 40 45 Feet
    tipe = fields.Str(required=True)  # Dry Rfr Tnk Flt o/d
    full_or_empty = fields.Str(required=True)
    activity = fields.Str(required=True)

    updated_at = fields.DateTime(required=True)