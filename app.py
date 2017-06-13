from flask import Flask, render_template, request, json, url_for, flash, redirect, session, abort
from flaskext.mysql import MySQL
from flask_login import LoginManager, current_user, login_required,login_user, logout_user, UserMixin, confirm_login, fresh_login_required
import flask_login
import os
from User import User
import os
from flask import Flask, request, redirect, url_for
from werkzeug.utils import secure_filename
import urllib2
import json
import math
import numpy as np
import scipy
from scipy import special, optimize
from scipy.stats import pearsonr
import csv
from datetime import datetime
import numpy as np
from StringIO import StringIO
from flask import Flask, stream_with_context
from werkzeug.datastructures import Headers
from werkzeug.wrappers import Response
from datetime import datetime

mysql = MySQL()

app=Flask(__name__)
 
# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'crawfordco'
app.config['MYSQL_DATABASE_PASSWORD'] = 'clcrwfrd'
app.config['MYSQL_DATABASE_DB'] = 'racing'
app.config['MYSQL_DATABASE_HOST'] = 'db-racingproj.cp9z0tdxgiyw.us-east-1.rds.amazonaws.com'
mysql.init_app(app)


########### Pages ####################
######################################
@app.route("/")
def main():
    return render_template('home.html')

@app.route('/showRaces')
def showRaces():
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()
        cursor2 = conn.cursor()
        

        print("hello")

        my_query = "SELECT * FROM Race"

        races = []

        cursor.execute(my_query)

        for (id, name, type, start_time, event, description) in cursor:
            my_query2 = "SELECT name, date FROM Event WHERE id="+str(event)
            cursor2.execute(my_query2)
            data = cursor2.fetchone()
            event = data[0] #event Name
            date = data[1] #date of the entire event

            date = date.strftime('%m/%d/%Y')
            
            race_info = {"id": id, "name": name, "type": type, "date": date, "event": event, "description": description}
            races.append(race_info)

        return render_template('races.html', races=races)

    except Exception as e:
        return json.dumps({'error':str(e)}), 404
    finally:
        cursor.close()

######################### Functions ##########
#############################################



if __name__=="__main__":
    app.secret_key = os.urandom(12)
    app.run()


