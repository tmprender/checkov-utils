from flask import Flask, request, jsonify
import subprocess
import json
import requests

app = Flask(__name__)

@app.route('/')
def index():
    result = subprocess.run(['checkov', '--help'], capture_output=True, text=True).stdout
    return result

@app.route('/checkov', methods = ['POST', 'GET'])
def checkov():
    # process input (encoded archive)
    
    # move to target directory

    # scan code
    result = subprocess.run(['checkov', '-d', './scan_target_dir/', '--output', 'json'], capture_output=True, text=True)
    scan  = json.loads(result.stdout)

    # return result text and exit code
    return scan

@app.route('/tf_run_task_review', methods = ['POST'])
def tf_run_task_review():

    # handle test/setup
    data = request.json
    if data['stage'] == 'test':
        return data
    
    # parse payload
    access_token = data['access_token']
    callback_url = data['task_result_callback_url']
    download_url = data.get('configuration_version_download_url')  # tar of code to scan, can be null
    tf_plan_dl_url = data.get('plan_json_api_url')  # json output, available in post-plan only
    

    # download config -- only post-plan (plain json) for now.. checkov() will handle tar extract needed for pre-plan
    headers = {
        'Content-Type': 'application/vnd.api+json',
        'Authorization': "Bearer " + access_token
    }
    response = requests.request("GET", tf_plan_dl_url, headers=headers)
    content = json.dumps(response.json())

    # pass to checkov
    with open("tfplan.json", "w") as f:
        f.write(content)

    result = subprocess.run(['checkov', '-f', './tfplan.json', '--output', 'json'], capture_output=True, text=True)
    scan = json.loads(result.stdout)

    # parse scan results
    scan_results = scan['results']

    scan_summary = scan['summary']
    str_summary = 'PASSED: {}, FAILED: {}, SKIPPED: {}'.format(scan_summary['passed'], scan_summary['failed'], scan_summary['skipped'])

    scan_status = 'passed'  # default to open for now.. should fail closed    
    if scan_summary['failed'] > 0:  # use soft-fail flag and exit code eventually
        scan_status = 'failed'

    # format response
    outcomes = []
    for check in scan_results['failed_checks']:
        outcome = {
            "type": "task-result-outcomes",
            "attributes": {
                "outcome-id": check['check_id'],
                "description": check['check_name'],
                "tags": [
                    {
                        "label": "resource",
                        "level": "info",
                        "value": check['resource']
                    },
                    {
                        "label": "file_path",
                        "level": "info",
                        "value": check['file_path']
                    },
                    {
                        "label": "guideline",
                        "level": "info",
                        "value": check.get('guideline')
                    }
                ]
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
    payload = json.dumps(payload)

    # return results to tfc/e
    response = requests.request('PATCH', callback_url, headers=headers, data=payload)
    return scan
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
