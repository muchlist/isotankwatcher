from marshmallow import Schema, fields

#Untuk load dari json saja , untuk dump langsung filter di mongodb + jsonify
class UserSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)
    email = fields.Email(required=False)
    