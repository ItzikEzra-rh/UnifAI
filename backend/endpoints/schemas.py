from marshmallow import Schema
from webargs import fields

class MessageSchema(Schema):
    id = fields.Str(required=True)  # The unique identifier of the message
    sender = fields.Str(required=True)  # The sender of the message, either 'user' or 'bot'
    text = fields.Str(required=True)  # The actual content of the message
