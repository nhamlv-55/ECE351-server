import sys
import subprocess
from flask import Flask, send_from_directory, jsonify, request
import time
import os
app = Flask(__name__)

UPLOAD_FOLDER = './test_uploads'
@app.route("/Lab3E")
def hello():
    return send_from_directory('static', 'Lab3E.html')

@app.route("/post/", methods = ["POST"])
def post():
    print("call post")
    input_content = request.form["input_content"]
    test = request.form["test"]
    lab = request.form["lab"]
    timestamp = time.time()
    filepath = os.path.join(UPLOAD_FOLDER, str(timestamp)+".f")
    with open(filepath, 'w') as f:
        f.write(input_content)
    print(filepath)
    print(input_content)
    command = "java -cp /home/ECE351-server/ece351-code/build:/home/ECE351-server/ece351-code/lib/* ece351.f.%s '%s' %s"%(lab, filepath, test)
    
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    p.wait()
    output = p.stdout.read().decode('utf-8')
    error = p.stderr.read().decode('utf-8')
    print(output)
    return jsonify(output = output, error = error)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=1234)
