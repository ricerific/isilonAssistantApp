from flask import Flask, render_template
import json
import subprocess


app = Flask(__name__)


isilonAssistant = "isilonAssistant.py"
templateAppA = "templateAppA.json"
templateAppB = "templateAppB.json"


# Show main page
@app.route("/")
def main():

    try:
    
        cmdA = subprocess.Popen(["type", templateAppA],shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdoutA,errorA = cmdA.communicate()
        outputA = stdoutA.splitlines()

        cmdB = subprocess.Popen(["type", templateAppB],shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdoutB,errorB = cmdB.communicate()
        outputB = stdoutB.splitlines()
        
        return render_template("index.html", outputA=outputA, outputB=outputB)

    except Exception as e:
        return render_template('error.html',error = "FAILED: Module / >> " + str(e))


# Show deployTemplateAppA page
@app.route("/deployTemplateAppA")
def deployTemplateAppA():

    try:
        
        cmd = subprocess.Popen(["python", isilonAssistant, "--file", templateAppA],shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout,error = cmd.communicate()
        outputLog = stdout.splitlines()
        errorLog = error.splitlines()

        return render_template("deployTemplateAppA.html", outputLog=outputLog, errorLog=errorLog)

    except Exception as e:
        return render_template('error.html',error = "FAILED: Module /deployTemplateAppA >> " + str(e))


# Show deployTemplateAppB page
@app.route("/deployTemplateAppB")
def deployTemplateAppB():

    try:
        
        cmd = subprocess.Popen(["python", isilonAssistant, "--file", templateAppB],shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout,error = cmd.communicate()
        outputLog = stdout.splitlines()
        errorLog = error.splitlines()

        return render_template("deployTemplateAppB.html", outputLog=outputLog, errorLog=errorLog)

    except Exception as e:
        return render_template('error.html',error = "FAILED: Module /deployTemplateAppB >> " + str(e))


if __name__ == "__main__":
    app.run()
