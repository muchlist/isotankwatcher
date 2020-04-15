from marshmallow import Schema, fields


class ContainerCheckInitSchema(Schema):
    checked_at = fields.DateTime(required=True)
    note = fields.Str(required=True)
    status = fields.Str(required=True)
    witness = fields.Str(required=True)

class ContainerCheckEditSchema(Schema):
    checked_at = fields.DateTime(required=True)
    note = fields.Str(required=True)
    status = fields.Str(required=True)
    witness = fields.Str(required=True)
    updated_at = fields.DateTime(required=True)

class ContainerCheckPassSchema(Schema):
    updated_at = fields.DateTime(required=True)