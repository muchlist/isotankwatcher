from marshmallow import Schema, fields

class ContainerApprovalSchema(Schema):
    updated_at = fields.DateTime(required=True)