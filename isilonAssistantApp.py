from flask import Flask, render_template, request, redirect, session
import json
import subprocess
from flaskext.mysql import MySQL
from werkzeug import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'hello world'

mysql = MySQL()
 
# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'mysqlUser'
app.config['MYSQL_DATABASE_PASSWORD'] = 'mysqlPass'
app.config['MYSQL_DATABASE_DB'] = 'BucketList'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

# Global parameters
isilonAssistant = "isilonAssistant.py"
templateAppA = "templateAppA.json"
templateAppB = "templateAppB.json"

# Show main page
@app.route("/")
def main():
    #return "Hello World!!!"
    return render_template("index.html")

# Show sign up page. The user enters inputs: name/username/password
@app.route('/showSignUp')
def showSignUp():
    return render_template('signUp.html')

# Take received inputs (name/username/password) from sign up page, and store into MySQL database
@app.route('/signUp', methods=['POST'])
def signUp():

    try:
        
        # Read the posted values from the UI
        _name = request.form['inputName']
        _email = request.form['inputEmail']
        _password = request.form['inputPassword']

        # Validate the received values
        if _name and _email and _password:
            # Connect to MySQL
            conn = mysql.connect()
            cursor = conn.cursor()
            # For some reason _hashed_password length is 96 characters, but still error out when storing into MySQL BucketList.tbl_user.user_password of varchar(255). So workaround is to store password as clear text.
            #_hashed_password = generate_password_hash(_password)
            _hashed_password = _password
            cursor.callproc('sp_createUser',(_name ,_email, _hashed_password))
            data = cursor.fetchall()

            # MySQL sp_createUser: INSERT INTO tbl_user (user_name, user_username, user_password) values(p_name,  p_username, p_password);
            # If return value is NULL, it means the stored procedure succeeded; else, return value is string "Username Exists !!"
            if len(data) is 0:
                # After data is inserted, commit the changes to the database
                conn.commit()
                return json.dumps({'app.py-signUp().message':'User created successfully !'})
            else:
                return json.dumps({'app.py-signUp().error1':str(data[0])})
                
            #return json.dumps({'app.py-signUp().html':'<span>All fields good !!</span>'})

        else:
            return json.dumps({'app.py-signUp().html':'<span>Enter the required fields</span>'})

    except Exception as e:
        return json.dumps({'app.py-signUp().error2':str(e)})
    finally:
        cursor.close() 
        conn.close()

# Show sign in page. The user enters inputs: username/password
@app.route('/showSignIn')
def showSignin():
    return render_template('signIn.html')

# Take the received inputs (username/password) from sign in page, and validate against MySQL database
@app.route('/validateLogin', methods=['POST'])
def validateLogin():
    try:
        _username = request.form['inputEmail']
        _password = request.form['inputPassword']
        
        # Connect to MySQL
        con = mysql.connect()
        cursor = con.cursor()
        cursor.callproc('sp_validateLogin',(_username,))
        data = cursor.fetchall()

        # MySQL sp_validateLogin: SELECT * FROM tbl_user WHERE user_username = p_username;
        # If return value is not NULL, then _username is found. Proceed to checking password.
        if len(data) > 0:
            # Checking password after username is correct. Since we didn't hash the password during INSERT, we will not hash it during SELECT
            #if check_password_hash(str(data[0][3]),_password):
            if str(data[0][3])== _password:
                # Set the session variable to the user_id after user login successful
                session['user'] = data[0][0]
                return redirect('/userHome')
            else:
                return render_template('error.html',error = _username + ' : Incorrect Password - Authorization Failed')
        else:
            return render_template('error.html',error = _username + ' : Incorrect Username - Authorization Failed')
            

    except Exception as e:
        return render_template('error.html',error = 'MySQL SP Exception: ' + str(e))
    finally:
        cursor.close()
        con.close()

# After user logs in successfully, call MySQL stored procedure to retrieve user's info (user_id, user_name, user_username, user_password) from the session variable (which stores the user_id)
# The fetched data from MySQL gets converted into a hash dictionary, and then converted into JSON, then return the JSON object
@app.route('/getUserData')
def getUserData():
    try:
        if session.get('user'):
            # Retrieve the user_id from the session variable
            _user = session.get('user')

            # User the user_id to obtain the remaining user's data from the database
            # MySQL sp_getUserData: SELECT * FROM tbl_user WHERE user_id = p_user_id;
            # Don't need to check for len(data) because the session variable is already valid, which means user_id exists in the database
            con = mysql.connect()
            cursor = con.cursor()
            cursor.callproc('sp_getUserData',(_user,))
            data = cursor.fetchall()

            # Convert MySQL fetched data into 2-dimensional hash dictionary
            user_dict = []
            for item in data:
                item_dict = {
                        'user_id': item[0],
                        'user_name': item[1],
                        'user_username': item[2],
                        'user_password': item[3]}
                user_dict.append(item_dict)

            # Return hash dictionary as JSON object
            return json.dumps(user_dict)
        else:
            return render_template('error.html', error = str(session.get('user')) + ' : Invalid Session - Access Unauthorized')
    except Exception as e:
        return render_template('error.html', error = 'MySQL SP Exception: ' + str(e))

# After user logs in successfully, redirect to the user's home page
@app.route('/userHome')
def userHome():
    #return render_template('userHome.html')

    # Check value of the session variable, which was set when user login successful
    # If value is valid, then go to user's home page; else, go to error page
    if session.get('user'):
    
        try:
            cmdA = subprocess.Popen(["type", templateAppA],shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            stdoutA,errorA = cmdA.communicate()
            outputA = stdoutA.splitlines()

            cmdB = subprocess.Popen(["type", templateAppB],shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            stdoutB,errorB = cmdB.communicate()
            outputB = stdoutB.splitlines()
			
            return render_template("userHome.html", outputA=outputA, outputB=outputB)

        except Exception as e:
            return render_template('error.html',error = "FAILED: Module / >> " + str(e))

    else:
        return render_template('error.html',error = str(session.get('user')) + ' : Invalid Session - Access Unauthorized')


# From the user's home page, initiate deployTemplateAppA
@app.route("/deployTemplateAppA")
def deployTemplateAppA():

    # Check value of the session variable, which was set when user login successful
    # If value is valid, then go to user's home page; else, go to error page
    if session.get('user'):
        
        try:
            
            cmd = subprocess.Popen(["python", isilonAssistant, "--file", templateAppA],shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            stdout,error = cmd.communicate()
            outputLog = stdout.splitlines()
            errorLog = error.splitlines()

            return render_template("deployTemplateAppA.html", outputLog=outputLog, errorLog=errorLog)

        except Exception as e:
            return render_template('error.html',error = "FAILED: Module /deployTemplateAppA >> " + str(e))

    else:
        return render_template('error.html',error = str(session.get('user')) + ' : Invalid Session - Access Unauthorized')


# From the user's home page, initiate deployTemplateAppB
@app.route("/deployTemplateAppB")
def deployTemplateAppB():

    # Check value of the session variable, which was set when user login successful
    # If value is valid, then go to user's home page; else, go to error page
    if session.get('user'):
        
        try:
            
            cmd = subprocess.Popen(["python", isilonAssistant, "--file", templateAppB],shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            stdout,error = cmd.communicate()
            outputLog = stdout.splitlines()
            errorLog = error.splitlines()

            return render_template("deployTemplateAppB.html", outputLog=outputLog, errorLog=errorLog)

        except Exception as e:
            return render_template('error.html',error = "FAILED: Module /deployTemplateAppB >> " + str(e))

    else:
        return render_template('error.html',error = str(session.get('user')) + ' : Invalid Session - Access Unauthorized')


# When user logs out, redirect to the main page
# Make session variable NULL
@app.route('/logout')
def logout():
    session.pop('user',None)
    return redirect('/')


if __name__ == "__main__":
    app.run()
