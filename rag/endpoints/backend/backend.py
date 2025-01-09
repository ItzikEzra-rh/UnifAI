import logging
import os
from flask import request, Blueprint
from flask import jsonify, Response
from webargs import fields
from helpers.apiargs import Fields, from_query, from_body
from be_utils.utils import json_response

rag_bp = Blueprint("rag", __name__)

@rag_bp.route("/", methods=["GET"])
def sanity_check():
    return 'There is access to API RAG Backend\n'