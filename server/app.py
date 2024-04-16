from flask import Flask, jsonify
import subprocess
import json

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
    data  = json.loads(result.stdout)

    # return result text and exit code
    return data

@app.route('/tf_run_task_review', methods = ['POST'])
def tf_run_task_review():
    # parse payload
    # download config
    # pass to checkov
    # format response
    # return results to tfc/e
    pass
    


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
