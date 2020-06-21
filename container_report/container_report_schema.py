from marshmallow import Schema, fields


class ContainerReportSchema(Schema):
    branch = fields.Str(required=True)
    start_date = fields.DateTime(required=True)
    end_date = fields.DateTime(required=True)


class ContainerInfoReportSchema(Schema):
    branch = fields.Str(required=True)
    start_date = fields.DateTime(required=True)
    end_date = fields.DateTime(required=True)
    activity = fields.Str(required=True)
    damaged = fields.Bool(required=True)
