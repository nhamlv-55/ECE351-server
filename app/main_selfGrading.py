import sys
import subprocess
from flask import Flask, send_from_directory, jsonify, request
import time
import os
import pymysql

app = Flask(__name__)
MAX = 10


@app.route("/Grading")
def hello():
    return send_from_directory('static', 'SelfGrading.html')

def check_commit_existance(student, commit):
    p = subprocess.Popen("cd /home/gradingCode/marking/students/%s; git checkout %s"%(student, commit), stderr = subprocess.PIPE, stdout=subprocess.PIPE, shell=True)        
    p.wait()
    output = p.stdout.read().decode('utf-8')
    err    = p.stderr.read().decode('utf-8')
    print("OUT:", output)
    print("ERR:", err)
    if "fatal: ref" in err or "error: path" in err:
        print("WTF")
        print(err.find("fatal"))
        return False
    return True

@app.route("/postGrade/", methods = ["POST"])
def post():
    print("call post grade")
    student = request.form["student"]
    lab = request.form["lab"]
    commit = request.form["commit"]

    if ";" in student or ";" in lab or ";" in commit:
        return jsonify(grade = "BAH!!! Are you trying to do SQL injection?", stacktrace = "", commit = "")


    #increase counter:
    conn = pymysql.connect(host='0.0.0.0', port=3306, user='root', passwd='ka1st', db='counter', charset='utf8')
    cur = conn.cursor()
    cur.execute("SELECT lab%s from counter WHERE studentid = '%s'"% (lab, student))
    counter = cur.fetchone()[0]
    if counter > MAX:
        return jsonify(grade = "You have self-graded %s times!"%MAX, stacktrace = "")
    else:
        cur.execute("UPDATE counter SET lab%s = lab%s + 1 WHERE studentid = '%s'"% (lab, lab, student))
        conn.commit()
    conn.close()

    clone_command = "cd /home/gradingCode/marking; rm -rf students/%s; git clone gitlab@git.uwaterloo.ca:ece351-1191/%s.git students/%s; "%(student, student, student)
    print(clone_command)
    p = subprocess.Popen(clone_command, shell=True)
    p.wait()

    # get the latest commit id if not provided
    res = check_commit_existance(student, commit)
    if res == False:
        return jsonify(grade = "The git commit that you provided is not correct.", stacktrace = "", commit = commit)
    print("Using commit:%s"%(commit))
    
    grading_command = "cd /home/gradingCode/marking/; ./grade.sh %s -s%s -f%s"%(lab, student, commit)
    print("Running grading script: %s"%grading_command)
    p = subprocess.Popen(grading_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    p.wait()

    path = '/home/gradingCode/marking/students/%s/marks/lab%s_marks/'%(student, lab)
    # read grade
    with open("%s/lab%s_final.csv"%(path, lab)) as f_grade:
        grade = f_grade.read()
    for filename in os.listdir(path):
        if "stacktrace" in filename:
            with open(os.path.join(path, filename), 'r') as f_stacktrace:
                stacktrace = f_stacktrace.read()
                #only show stacktrace when build not success
                if "[javac]" not in stacktrace:
                    stacktrace = "BUILD SUCCESSFUL"
    stacktrace = "You have used %s out of %s tokens for lab %s\n-------------------------------\n"%(str(counter), str(MAX), lab)+stacktrace
    return jsonify(grade = grade, stacktrace = stacktrace, commit = commit)
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=80)
