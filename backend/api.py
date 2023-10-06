import json
import logging

from flask import Flask, jsonify, request
from flask_cors import CORS

import validation_interface
import verbalization_interface

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)


@app.route("/", methods=["GET"])
def base():
    return jsonify({"response": "Hello from the QuaRe backend!"})


@app.route("/project-type-specifications", methods=["GET"])
def project_type_specifications():
    return jsonify(validation_interface.get_project_type_specifcations())


@app.route("/validate", methods=['POST'])
def validate():

    request_data = json.loads(request.data)
    github_access_token = request_data["accessToken"]
    repo_name = request_data["repoName"]
    repo_type = request_data["repoType"]
    method = request_data["method"]

    returncode, report = validation_interface.run_validator(github_access_token, repo_name, repo_type, method)
    verbalized = verbalization_interface.run_verbalizer(report, repo_name, repo_type, method)

    results = {"repoName": repo_name, "returnCode": returncode,
               "report": report, "verbalized": verbalized}

    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
