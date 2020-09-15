from flask import jsonify, request

from api._index import app
from api.streets_utils import get_suggestions
import logging

logger = logging.getLogger()


@app.route('/api/suggestions', methods=['POST'])
def get_completions():
    text = request.json.get('text')
    if 'max' in request.json:
        max_suggestions = request.json.get('max')
        suggestions = get_suggestions(text, max_suggestions)
    else:
        suggestions = get_suggestions(text)
    res = {}
    if 'request_id' in request.json:
        res['request_id'] = request.json.get('request_id')
    res['suggestions'] = suggestions
    return jsonify(res)
