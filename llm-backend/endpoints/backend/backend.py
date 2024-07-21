import logging
import os
from flask import Blueprint
from flask import jsonify, Response
from webargs import fields

backend_bp = Blueprint("backend", __name__)

@backend_bp.route("/", methods=["GET"])
def sanity_check():
    return 'There is access to api backend'