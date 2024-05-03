import os
import subprocess
import json
import base64
import tarfile
import shutil
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    usage_instructions = {
        "welcome": "Welcome to the Checkov API!",
        "instructions": {
            "To scan your Terraform code": "Send a POST request to /checkov with a JSON payload containing your base64-encoded .tar.gz file and optional Checkov CLI flags.",
            "Format example": {
                "file": "<base64_encoded_tar_gz_data>",
                "flags": ["--flag1", "--flag2", "value2", "--flag3=value3"]
            },
            "To use Checkov CLI locally": "Run 'checkov --help' on your local machine for a list of available Checkov commands and flags."
        },
        "more_info": "For more details on Checkov, visit https://www.checkov.io/"
    }
    return jsonify(usage_instructions)

@app.route('/checkov', methods=['POST'])
def checkov_api():
    data = request.get_json()
    # check request for required args
    if not data or 'flags' not in data or 'file' not in data:
        return jsonify({"error": "Invalid request. JSON with 'flags' and 'file' required."}), 400

    # create temporary directory
    target_dir = './temp_dir'
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    # unpack tar and scan
    try:
        decode_and_unpack_tar_gz(data['file'], target_dir)
        scan_results = run_checkov(target_dir, data['flags'], is_file=False)
        return jsonify({"scan_result": scan_results}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Checkov scan failed.", "details": e.stderr}), 500
    
    # clean up temporary directory
    finally:
        shutil.rmtree(target_dir, ignore_errors=True)


@app.route('/tf_run_task_review', methods=['POST'])
def tf_run_task_review():
    data = request.json

    # handle test/setup
    if data['stage'] == 'test':
        return data
    
    # parse payload
    access_token = data['access_token']
    callback_url = data['task_result_callback_url']
    download_url = data.get('configuration_version_download_url')  # tar of code to scan, can be null
    tf_plan_dl_url = data.get('plan_json_api_url')  # json output, available in post-plan only
    
    headers = {
        'Content-Type': 'application/vnd.api+json',
        'Authorization': "Bearer " + access_token
    }
    #pre_plan
    if data['stage'] == 'pre_plan':
        if download_url:
            # Download and extract tar.gz
            try:
                response = requests.get(download_url, headers=headers)
                response.raise_for_status()
                target_dir = './temp_dir'
                os.makedirs(target_dir, exist_ok=True)
                decode_and_unpack_tar_gz(response.content, target_dir, is_base64_encoded=False)
                # Run Checkov on the directory
                scan = run_checkov(target_dir, cli_flags=None, is_file=False)
                # Cleanup
                shutil.rmtree(target_dir)
            except Exception as e:
                return jsonify({"error": e}), 500
        else:
            return jsonify({"error": "No configuration version download URL provided for pre-plan."}), 400
    
    # post_plan    
    elif data['stage'] == 'post_plan':
        # Download the plan JSON
        try:
            response = requests.get(tf_plan_dl_url, headers=headers)
            response.raise_for_status()
            plan_json = response.json()
            with open("tfplan.json", "w") as f:
                json.dump(plan_json, f)
            # Run Checkov on the plan file
            scan = run_checkov("tfplan.json", None, is_file=True)
            os.remove("tfplan.json")
        except Exception as e:
            return jsonify({"error": e}), 500
    # invalid stage / not supported
    else:
        return jsonify({"error": "Invalid stage."}), 400

    # parse checkov scan results
    scan_results = scan['results']

    scan_summary = scan['summary']
    str_summary = 'PASSED: {}, FAILED: {}, SKIPPED: {}'.format(scan_summary['passed'], scan_summary['failed'], scan_summary['skipped'])

    scan_status = 'passed'  # default to open for now.. should fail closed    
    if scan_summary['failed'] > 0:  # use soft-fail flag and exit code eventually
        scan_status = 'failed'

    # format response for TFC/E
    outcomes = []
    for check in scan_results['failed_checks']:
        outcome = {
            "type": "task-result-outcomes",
            "attributes": {
                "outcome-id": check['check_id'],
                "description": check['check_name'],
                "url": check.get('guideline'),
                "body": "Checkov found an issue with {} in {}.".format(check['resource'], check['file_path'])
            }          
        }
        outcomes.append(outcome)

    payload = {
        "data": {
            "type": "task-results",
            "attributes": {
                "status": scan_status,
                "message": str_summary,
                "url": "https://checkov.io/",
            },
            "relationships": {
                "outcomes":{
                    "data": outcomes
                }
            }
        }
    }

    # Return results to tfc/e
    response = requests.patch(callback_url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    return jsonify(scan)

# Internals

def decode_and_unpack_tar_gz(file_content, target_dir, is_base64_encoded=True):
    # Decode the base64-encoded file if necessary
    if is_base64_encoded:
        try:
            file_data = base64.b64decode(file_content)
        except base64.binascii.Error as e:
            raise ValueError("Invalid base64 encoding") from e
    else:
        file_data = file_content

    # Write the binary data to a temporary file
    temp_tar_path = os.path.join(target_dir, 'temp_file.tar.gz')
    with open(temp_tar_path, 'wb') as f:
        f.write(file_data)

    # Extract the tar.gz file
    try:
        with tarfile.open(temp_tar_path, 'r:gz') as tar:
            tar.extractall(path=target_dir)
    finally:
        os.remove(temp_tar_path)

def run_checkov(target, cli_flags, is_file=False):
    if cli_flags is None:
        cli_flags = []
    # Determine the Checkov scan target flag based on the input
    target_flag = '-f' if is_file else '-d'
    # Run the Checkov scan
    result = subprocess.run(
        ['checkov', target_flag, target, '--output', 'json'] + cli_flags,
        capture_output=True,
        text=True
    )
    # if result.returncode != 0:
    #     raise subprocess.CalledProcessError(result.returncode, result.args, output=result.stdout, stderr=result.stderr)
    return json.loads(result.stdout)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
