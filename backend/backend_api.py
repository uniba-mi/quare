#!/usr/bin/env python3

import json
import logging

from flask import Flask, jsonify, request
from flask_cors import CORS

import validation_interface

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)


@app.route("/", methods=['GET'])
def hello_world():
    return jsonify({"response": "Hello, World!"})


@app.route("/project-types-specifications", methods=['GET'])
def repo_types():
    return jsonify({"projectTypeSpecifications": validation_interface.get_project_type_specifcations()})


@app.route("/validate", methods=['POST'])
def validate():

    request_data = json.loads(request.data)
    github_access_token = request_data["accessToken"]
    repo_name = request_data["repoName"]
    repo_type = request_data["repoType"]
    method = request_data["method"]

    results = validation_interface.run_validator(
        github_access_token, repo_name, repo_type, method)

    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
