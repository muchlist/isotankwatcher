from marshmallow import Schema, fields

# Untuk load dari json saja , untuk dump langsung filter di mongodb + jsonify


class UserRegisterSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)
    email = fields.Email(required=False)
    phone = fields.Str(required=False)
    name = fields.Str(required=True)
    isAdmin = fields.Bool(required=False)
    isAgent = fields.Bool(required=False)
    isTally = fields.Bool(required=True)
    isForeman = fields.Bool(required=False)
    company = fields.Str(required=True)
    position = fields.Str(required=True)
    branch = fields.List(fields.Str, required=True)  # sampit, bagendang


class UserEditSchema(Schema):
    email = fields.Email(required=True)
    isAdmin = fields.Bool(required=True)
    name = fields.Str(required=True)
    phone = fields.Str(required=True)
    isAgent = fields.Bool(required=True)
    isTally = fields.Bool(required=True)
    isForeman = fields.Bool(required=True)
    company = fields.Str(required=True)
    position = fields.Str(required=True)
    branch = fields.List(fields.Str, required=True)  # sampit, bagendang


class UserLoginSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)


class UserChangePassSchema(Schema):
    password = fields.Str(required=True)
    new_password = fields.Str(required=True)
