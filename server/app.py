from flask import Flask, jsonify
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    result = subprocess.run(['checkov', '--help'], capture_output=True, text=True).stdout
    return result

@app.route('/checkov', methods = ['POST'])
def checkov():

    result = subprocess.run(['checkov', '-d', '.'], capture_output=True, text=True).stdout
    return result
    
    #data = {}

    # code for receiving data
    # processing data and saving results in dictionary 

    #return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
