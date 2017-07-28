from flask import Flask, render_template, request, json, url_for, flash, redirect, session, abort, make_response  
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
from flask import session
from flask import send_from_directory


mysql = MySQL()
login_manager = LoginManager()

app=Flask(__name__, static_folder="static")
 
# MySQL configurations
app.config['UPLOAD_FOLDER'] = '/tmp'
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'csv'])

app.config['MYSQL_DATABASE_USER'] = 'crawfordco'
app.config['MYSQL_DATABASE_PASSWORD'] = 'clcrwfrd'
app.config['MYSQL_DATABASE_DB'] = 'racing'
app.config['MYSQL_DATABASE_HOST'] = 'db-racingproj.cp9z0tdxgiyw.us-east-1.rds.amazonaws.com'
mysql.init_app(app)
login_manager.init_app(app)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def calc_age(bday_year, event_year):
    return int(event_year)-int(bday_year)

########### Show Pages ####################
##########################################
@app.route("/")
def main():
    if 'error' in request.args:
        error = request.args['error']
    else:
        error="None"
    return render_template('home.html', error=error)

###################################################### LOGIN STUFF ################################################################

@login_manager.user_loader
def load_user(username1):
    conn=mysql.get_db()
    cursor=conn.cursor()
    cursor.execute("SELECT * from Admin WHERE username= '{username1}'".format(username1=username1))
    data=cursor.fetchone()
    u=User(data[0],data[1],data[2],data[3],data[4])
    return u

@app.route("/showLogin/<page>")
def showLogin(page=None):
    return render_template('login.html', page=page)

@app.route('/login/<page>', methods=['POST'])
def login(page=None):
    passwd1=request.form['password']
    username1=request.form['username']

    if passwd1 == "" or username1 == "":
        error = "You must fill out ALL fields in order to login!"
        return render_template('login.html', error=error)

    if username1 and passwd1:
        conn=mysql.get_db()
        cursor=conn.cursor()

        cursor.execute("SELECT * from Admin WHERE username= '{username1}' AND password='{passwd1}'".format(username1=username1,passwd1=passwd1))
        data=cursor.fetchone()
        
        if data == None:
            error = "Wrong username or password! Try again!"
            return render_template('login.html', error=error)

        print(data)

        u=User(data[0],data[1],data[2],data[3],data[4])
        print u
        print("before match check")
        print(u.username, username1, u.passwd, passwd1)
        if u.username == username1 and u.passwd==passwd1:
            print("matches!")
            session['logged_in']=True
            login_user(u,True)
        else:
            error = "Wrong username or password! Try again!"
            return render_template('login.html', error=error)

        if page=="main":
            return main()
        elif page=="events":
            return showEvents()
        elif page=="races":
            return showRaces()
        elif page=="participants":
            return showParticipants()

@app.route('/logout')
def logout():
    session['logged_in'] = False
    logout_user()
    return render_template('home.html')

###################################################### EVENT STUFF ################################################################

@app.route("/showEventForm")
def showEventForm():
    return render_template('eventForm.html')

@app.route("/eventForm", methods=['POST', 'GET']) #CREATE AN EVENT
def eventForm():
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()
        
        event_name = request.form['event_name']
        event_city = request.form['event_city']
        event_state = request.form['event_state']
        event_date = request.form['event_date']
        event_description = request.form['event_description']

        print(event_name) 

        if (event_name == "" or event_city == "" or event_state == "None" or event_date == ""):
            error = 'ALL of the required fields must be filled out!'
            return render_template('eventForm.html', error=error)

        if event_description == "":
            event_description = 'None'

        event_name=event_name.replace("'","''")
        event_city=event_city.replace("'","''")
        event_description=event_description.replace("'","''")

        print(event_city)

        my_query="SELECT id, date FROM Event WHERE name='"+event_name+"' AND city='"+event_city+"' AND state='"+event_state+"' AND date='"+event_date+"'"
        cursor.execute(my_query)
        if cursor.rowcount > 0:
            data=cursor.fetchone()
            event_id=data[0]
            event_date_1=data[1]
            dup_error="True"
            event_date_1 = event_date_1.strftime('%m/%d/%Y')
            return render_template('eventForm.html', dup_error=dup_error, event_name=event_name, event=event_id, event_date=event_date_1,
             event_city=event_city, event_state=event_state)
        
        print("made thru select")
        my_query = ("INSERT INTO Event (name, city, state, date, description) VALUES ('"+event_name+"','"+event_city+"','"+
            event_state+"','"+event_date+"','"+event_description+"')")

        print(my_query)
        
        cursor.execute(my_query)
        conn.commit()

        my_query="SELECT id FROM Event WHERE name='"+event_name+"' AND city='"+event_city+"' AND state='"+event_state+"' AND date='"+event_date+"'"
        cursor.execute(my_query)
        event_id=cursor.fetchone()[0]

        success = "The Event '"+event_name+"' was successfully created!"
        return render_template("raceForm.html", success=success, event_id=event_id, event_name=event_name) ### GO STRAIGHT TO CREATING RACES FOR THIS EVENT
    except Exception as e:
        error = 'This Event was not properly created!'
        return json.dumps({'error':str(e)}), 404
        #return render_template('eventForm.html', error=error)
    finally:
        cursor.close()

@app.route('/showEvents')
def showEvents():
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()

        print("hello")

        my_query = "SELECT * FROM Event ORDER BY date desc, name"

        events = []

        cursor.execute(my_query)

        for (id, event_name, event_city, event_state, event_date, event_description) in cursor:
            print(len(event_description))
            if len(event_description)>40:
                event_description=event_description[1:40]
                event_description+="...(click on event name to see more)"
            event_date = event_date.strftime('%m/%d/%Y')
            event_info = {"id": id, "name": event_name, "city": event_city, "state": event_state, "date": event_date, "description": event_description}
            events.append(event_info)

        if 'success' in request.args:
            success = request.args['success']
            return render_template('events.html', events=events, success=success)
        else:
            return render_template('events.html', events=events)

    except Exception as e:
        return json.dumps({'error':str(e)}), 404
    finally:
        cursor.close()

#################################################
@app.route("/setUpEvent")                       #
def setUpEvent():                               #
    return render_template('setUpEvent.html')   #
#################################################

@app.route('/showRegisterForEventSelect') #show all races in dropdown on event select screen for event registration
def showRegisterForEventSelect():
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()

        my_query = "SELECT * FROM Event ORDER BY date desc"
        cursor.execute(my_query)
        events = []

        print("hello")

        for (id, event_name, event_city, event_state, event_date, event_description) in cursor:
            event_info = {"id": id, "name": event_name, "date": event_date, "city": event_city, "state": event_state}
            events.append(event_info)

        return render_template('registerForEventSelect.html', events=events)
    except Exception as e:
        error = 'Could not get events properly'
        return render_template('registerForEventSelect.html', error=error)
    finally:
        cursor.close()

@app.route("/showRegisterForEvent", methods=['POST', 'GET']) #show the registration page for events
def showRegisterForEvent():
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()

        event_id = request.form['event']

        my_query = "SELECT * FROM Event ORDER BY date desc"
        cursor.execute(my_query)
        events = []

        for (id, event_name, event_city, event_state, event_date, event_description) in cursor:
            event_info = {"id": id, "name": event_name, "date": event_date, "city": event_city, "state": event_state}
            events.append(event_info)

        if event_id=="None":
            error='Please select an event, if no events are displayed you may need to create a new event'
            return render_template('registerForEventSelect.html', error=error, events=events)


        my_query = "SELECT * FROM Registered WHERE event="+event_id+" ORDER BY last_name, first_name"
        cursor.execute(my_query)
        registered_people = []

        for (id, first_name, last_name, bib, rfid_tag, event, gender, age, license, phone, email, birthday) in cursor:
            people_info = {"id": id, "first_name": first_name, "last_name": last_name, "bib": bib, "license": license, "rfid_tag": rfid_tag}
            registered_people.append(people_info)

        my_query="SELECT name FROM Event WHERE id="+event_id
        cursor.execute(my_query)
        event_name=cursor.fetchone()[0]

        my_query="SELECT * FROM Race WHERE event="+event_id
        cursor.execute(my_query)
        races = []

        for(id, name, type, start_time, event, description) in cursor:
            race_info={"id": id, "name": name}
            races.append(race_info)

        return render_template('registerForEvent.html', registered_people=registered_people, event_id=event_id, event_name=event_name, races=races)
    except Exception as e:
        error = 'Registration could not be shown!'
        return json.dumps({'error':str(e)}), 404
        #return render_template('registerForEventSelect.html', error=error, events=events)

@app.route("/registerForEvent/<event_id>", methods=['POST', 'GET'])
def registerForEvent(event_id=None):
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()

        print(event_id)

        my_query = "SELECT * FROM Registered WHERE event="+event_id+" ORDER BY last_name, first_name"
        cursor.execute(my_query)
        registered_people = []

        for (id, first_name, last_name, bib, rfid_tag, event, gender, age, license, phone, email, birthday) in cursor:
            people_info = {"id": id, "first_name": first_name, "last_name": last_name, "bib": bib, "license": license, "rfid_tag": rfid_tag}
            registered_people.append(people_info)

        my_query="SELECT name, date FROM Event WHERE id="+event_id
        cursor.execute(my_query)
        for (name, date) in cursor:
            event_name=name
            event_date=date

        my_query="SELECT * FROM Race WHERE event="+event_id
        cursor.execute(my_query)
        races = []

        for(id, name, type, start_time, event, description) in cursor:
            race_info={"id": id, "name": name}
            races.append(race_info)

        print('made thru first')
        print(event_name)

        first_name = request.form['first_name']
        last_name = request.form['last_name']
        bib = request.form['bib']
        rfid_tag = request.form['rfid_tag']
        gender = request.form['gender']
        birthday = request.form['birthday']

        bday_year = datetime.strptime(birthday, '%Y-%m-%d')
        bday_year=bday_year.strftime('%Y')
        event_year = event_date.strftime('%Y')
        age=str(calc_age(bday_year, event_year))

        license = request.form['license']
        phone = request.form['phone']
        email = request.form['email']
        race_ids=request.form.getlist('races')
        print(race_ids)
        #signed_races=request.form.getlist('races')

        first_name=first_name.replace("'","''")
        last_name=last_name.replace("'","''")

        ################################## error checking ##########################################################

        #if all the required fields aren't filled out
        if (first_name=="" or last_name=="" or bib=="" or rfid_tag=="" or gender=="None" or age=="0" or license=="" or phone=="" or email==""):
            error = 'ALL of the required fields must be filled out!'
            return render_template('registerForEvent.html', error=error, registered_people=registered_people, event_id=event_id, event_name=event_name, races=races)
        
        #if someone is already registered with input bib number in this event
        my_query=("SELECT COUNT(*), Registered.first_name, Registered.last_name FROM Registered, Event WHERE Registered.event=Event.id AND Registered.bib="
        +bib+" AND Event.id="+event_id)
        cursor.execute(my_query)
        data=cursor.fetchone()
        if data[0] > 0:
            error=data[1]+" "+data[2]+" is already registered with Bib #"+bib+ " in "+event_name
            return render_template('registerForEvent.html', error=error, registered_people=registered_people, event_id=event_id, event_name=event_name, races=races)
        
        #if someone is already registered with input rfid tag in this event
        my_query="SELECT COUNT(*), Registered.first_name, Registered.last_name FROM Registered, Event WHERE Registered.event=Event.id AND Registered.rfid_tag="+rfid_tag+" AND Event.id="+event_id
        cursor.execute(my_query)
        data=cursor.fetchone()
        if data[0] > 0:
            error=data[1]+" "+data[2]+" is already registered with RFID Tag "+rfid_tag+ " in "+event_name
            return render_template('registerForEvent.html', error=error, registered_people=registered_people, event_id=event_id, event_name=event_name, races=races)
        
        #if someone is already registered with input LICENSE in this event
        my_query="SELECT COUNT(*), Registered.first_name, Registered.last_name FROM Registered, Event WHERE Registered.event=Event.id AND Registered.license="+license+" AND Event.id="+event_id
        cursor.execute(my_query)
        data=cursor.fetchone()
        if data[0] > 0:
            error=data[1]+" "+data[2]+" is already registered with License #"+license+ " in "+event_name
            return render_template('registerForEvent.html', error=error, registered_people=registered_people, event_id=event_id, event_name=event_name, races=races)
        
        my_query = ("INSERT INTO Registered (first_name, last_name, bib, rfid_tag, event, gender, age, license, phone, email, birthday) VALUES ('"+first_name+"','"
            +last_name+"','"+bib+"','"+rfid_tag+"','"+event_id+"','"+gender+"','"+age+"','"+license+"','"+phone+"','"+email+"','"+birthday+"')")
        cursor.execute(my_query)
        conn.commit()

        reg_for_races=" and was signed up for these races: "
        
        for race_id in race_ids:
            my_query="SELECT id FROM Registered WHERE bib='"+str(bib)+"' AND rfid_tag='"+str(rfid_tag)+"' AND event='"+str(event_id)+"'"
            cursor.execute(my_query)
            registration_id=cursor.fetchone()[0]
            print(registration_id)

            my_query="SELECT name FROM Race WHERE id="+str(race_id)
            cursor.execute(my_query)
            if race_id!=race_ids[-1]:
                reg_for_races+="'"+str(cursor.fetchone()[0])+"', "
            else:
                reg_for_races+="'"+str(cursor.fetchone()[0])+"'"

            my_query=("INSERT INTO Participant (race, registration_id) VALUES ('"+str(race_id)+"','"+str(registration_id)+"')")
            cursor.execute(my_query)
            conn.commit()

        success = "Registration complete! "+first_name+" "+last_name+" was registered for "+event_name
        if race_ids:
            success+= reg_for_races
        return render_template("registerForEvent.html", success=success, registered_people=registered_people, event_id=event_id, event_name=event_name, races=races)
    except Exception as e:
        error = 'This person was not registered correctly!'
        return json.dumps({'error':str(e)}), 404
        #return render_template('registrationForm.html', error=error, registered_people=registered_people, event_id=event_id, races=races)
    finally:
        cursor.close()

@app.route("/deleteEvent/<event_id>", methods=['POST', 'GET'])
def deleteEvent(event_id=None):
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()
        cursor2 = conn.cursor()

        print(event_id)

        my_query = "SELECT name FROM Event WHERE id="+str(event_id)
        cursor.execute(my_query)
        event_name=cursor.fetchone()[0]

        #####FIRST GO DELETE ALL PARTICIPANT RACERS FOR EACH RACE IN THIS EVENT
        my_query = "SELECT id FROM Race WHERE event="+str(event_id)
        cursor.execute(my_query)
        for race_id in cursor:
            #### FOR EACH RACE:
            my_query="DELETE FROM Participant WHERE race="+str(race_id)
            cursor2.execute(my_query)

        #### THEN GO DELETE ALL REGISTERED IN EVENT
        my_query="DELETE FROM Registered WHERE event="+str(event_id)
        cursor.execute(my_query)

        #### FINALLY GO DELETE ALL RACES IN EVENT
        my_query="DELETE FROM Race WHERE event="+str(event_id)
        cursor.execute(my_query)

        my_query = "DELETE FROM Event WHERE id="+str(event_id)
        cursor.execute(my_query)
        
        conn.commit()

        success=event_name+" was successfully deleted!"
        return redirect(url_for('showEvents', success=success))
    except Exception as e:
        error = 'Could not be properly deleted!'
        return json.dumps({'error':str(e)}), 404
        #return render_template('registrationForm.html', error=error, registered_people=registered_people, event_id=event_id, races=races)
    finally:
        cursor.close()

@app.route("/showEditEvent/<event_id>", methods=['POST', 'GET'])
def showEditEvent(event_id=None):
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()

        print(event_id)

        my_query = "SELECT * FROM Event WHERE id="+str(event_id)
        cursor.execute(my_query)
        for (id, name, city, state, date, description) in cursor:
            event_id=id
            event_name=name
            event_city=city
            event_state=state
            event_date=date
            event_description=description

        return render_template("editEvent.html", event_id=event_id, event_name=event_name, event_city=event_city, event_state=event_state,
            event_date=event_date, event_description=event_description)
    except Exception as e:
        error = 'Could not be properly edited!'
        return json.dumps({'error':str(e)}), 404
        #return render_template('registrationForm.html', error=error, registered_people=registered_people, event_id=event_id, races=races)
    finally:
        cursor.close()

@app.route("/editEvent/<event_id>", methods=['POST', 'GET'])
def editEvent(event_id=None):
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()

        print(event_id)

        event_name = request.form['event_name']
        event_city = request.form['event_city']
        event_state = request.form['event_state']
        event_date = request.form['event_date']
        event_description = request.form['event_description']

        my_query = "SELECT * FROM Event WHERE id="+str(event_id)
        cursor.execute(my_query)
        for (id, name, city, state, date, description) in cursor:
            if (event_name!=name or event_city!=city or event_state!=state or event_date!=event_date or event_description!=description):
                my_query=("UPDATE Event SET name='"+event_name+"', city='"+event_city+"', state='"+event_state+"',"+
                    " date='"+event_date+"', description='"+event_description+"' WHERE id="+event_id)
                cursor.execute(my_query)
                conn.commit()

        success="Changes made to "+event_name+" successfully!"
        return redirect(url_for('showEvents', success=success))
    except Exception as e:
        error = 'Could not be properly edited!'
        return json.dumps({'error':str(e)}), 404
        #return render_template('registrationForm.html', error=error, registered_people=registered_people, event_id=event_id, races=races)
    finally:
        cursor.close()

###################################################### RACE STUFF ################################################################

@app.route('/showRaceFormSelect') #show all races in dropdown on event select screen for creating races
def showRaceFormSelect():
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()

        my_query = "SELECT * FROM Event ORDER BY date desc"
        cursor.execute(my_query)
        events = []

        print("hello")

        for (id, event_name, event_city, event_state, event_date, event_description) in cursor:
            event_info = {"id": id, "name": event_name, "date": event_date, "city": event_city, "state": event_state}
            events.append(event_info)

        return render_template('raceFormSelect.html', events=events)
    except Exception as e:
        error = 'Could not get events properly'
        return render_template('raceFormSelect.html', error=error)
    finally:
        cursor.close()

@app.route("/showRaceForm", methods=['POST', 'GET']) #show the raceForm page after selecting an event to add races to
def showRaceForm():
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()

        event_id = request.form['event']

        my_query = "SELECT * FROM Event ORDER BY date desc"
        cursor.execute(my_query)
        events = []

        for (id, event_name, event_city, event_state, event_date, event_description) in cursor:
            event_info = {"id": id, "name": event_name, "date": event_date, "city": event_city, "state": event_state}
            events.append(event_info)

        print("hello3")

        if event_id=="None":
            error='Please select an event, if no events are displayed you may need to create a new event'
            return render_template('raceFormSelect.html', error=error, events=events)


        my_query="SELECT name FROM Event WHERE id="+event_id
        cursor.execute(my_query)
        event_name=cursor.fetchone()[0]

        return render_template('raceForm.html', event_id=event_id, event_name=event_name)
    except Exception as e:
        error = 'Race registration could not be shown!'
        #return json.dumps({'error':str(e)}), 404
        return render_template('raceFormSelect.html', error=error, events=events)

@app.route("/raceForm/<race_event>", methods=['POST', 'GET']) #CREATE A RACE
def raceForm(race_event=None):
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()
        
        my_query = "SELECT * FROM Event ORDER BY name"
        cursor.execute(my_query)
        events = []

        for (id, event_name, event_state, event_city, event_date, event_description) in cursor:
            event_info = {"id": id, "name": event_name}
            events.append(event_info)

        race_name = request.form['race_name']
        race_type = request.form['race_type']
        race_description = request.form['race_description']
        print("got everything")

        if (race_name == "" or race_type == "None" or race_event == "None"):
            error = 'ALL of the required fields must be filled out!'
            return render_template('raceForm.html', error=error, events=events)

        if race_description == "":
            race_description = 'None'

        my_query="SELECT name FROM Event WHERE id="+race_event
        cursor.execute(my_query)
        event_name=cursor.fetchone()[0]
        print(event_name)

        my_query="SELECT id FROM Race WHERE Race.name='"+race_name+"' AND Race.event="+race_event
        cursor.execute(my_query)
        if cursor.rowcount > 0:
            race_id=cursor.fetchone()[0]
            print(race_id)
            dup_error="True"
            return render_template('raceForm.html', dup_error=dup_error, events=events, event_name=event_name, race_name=race_name, race=race_id, event_id=race_event)

        my_query = ("INSERT INTO Race (name, type, event, description) VALUES ('"+race_name+"','"+race_type+"','"+
            race_event+"','"+race_description+"')")

        print(my_query)
        
        cursor.execute(my_query)
        conn.commit()

        success = "'"+race_name+"' was successfully created and added to "+event_name+"!"
        return render_template("raceForm.html", success=success, events=events, event_name=event_name, event_id=race_event)
    except Exception as e:
        error = 'This Race was not properly created!'
        return json.dumps({'error':str(e)}), 404
        #return render_template('raceForm.html', error=error, events=events)
    finally:
        cursor.close()

@app.route('/showRaces/<race_event>')
def showRaces(race_event=None):
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()
        cursor2 = conn.cursor()

        if 'success' in request.args:
            success = request.args['success']
        else:
            success="None"

        if 'error' in request.args:
            error = request.args['error']
        else:
            error="None"

        participants="false"
    
        my_query="SELECT id, name, city, state, date, description FROM Event WHERE Event.id="+race_event
        cursor.execute(my_query)
        
        for (id, name, city, state, date, description) in cursor:
            eventname=name
            event_date=date
            event_date = event_date.strftime('%m/%d/%Y')
            event_id=id
            event_city = city
            event_state = state
            event_description = description

        my_query="SELECT COUNT(*) FROM Registered WHERE event="+str(event_id)
        cursor.execute(my_query)
        registered_racers=cursor.fetchone()[0]
        
        my_query="SELECT * FROM Registered WHERE event="+str(event_id)
        cursor.execute(my_query)
        if cursor.rowcount>0:
            participants="true"
        
        my_query = "SELECT Race.* FROM Event, Race WHERE Race.event="+race_event+" AND Event.id=Race.event ORDER BY date desc, Event.name, Race.name"

        races = []

        cursor.execute(my_query)

        if cursor.rowcount == 0:
            print("no res")
            return render_template('races.html', noResults="true", eventname=eventname, event_id=event_id, participants=participants, 
                event_date=event_date, event_city=event_city, event_state=event_state, event_description=event_description,
                registered_racers=registered_racers, success=success, error=error)

        for (id, race_name, type, start_time, event, description) in cursor:
            '''my_query2 = "SELECT name, date FROM Event WHERE id="+str(event)
            cursor2.execute(my_query2)
            data = cursor2.fetchone()
            event = data[0] #event Name
            date = data[1] #date of the entire event
            '''
            
            race_info = {"id": id, "name": race_name, "type": type, "date": event_date, "event": eventname, "description": description}
            races.append(race_info)

        return render_template('races.html', races=races, eventname=eventname, event_id=event_id, participants=participants,
            event_date=event_date, event_city=event_city, event_state=event_state, event_description=event_description,
            registered_racers=registered_racers, success=success, error=error)
    except Exception as e:
        return json.dumps({'error':str(e)}), 404
    finally:
        cursor.close()

@app.route('/showRegisterForRaceSelect') #show all races in dropdown on event select screen for race registration
def showRegisterForRaceSelect():
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()

        my_query = "SELECT * FROM Event ORDER BY date desc"
        cursor.execute(my_query)
        events = []

        print("hello")

        for (id, event_name, event_city, event_state, event_date, event_description) in cursor:
            event_info = {"id": id, "name": event_name, "date": event_date, "city": event_city, "state": event_state}
            events.append(event_info)

        return render_template('registerForRaceSelect.html', events=events)
    except Exception as e:
        error = 'Could not get events properly'
        return render_template('registerForRaceSelect.html', error=error)
    finally:
        cursor.close()

@app.route("/showRegisterForRace", methods=['POST', 'GET']) #show the registration page for races and show all races for the given event in dropdown
def showRegisterForRace():
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()

        event_id = request.form['event']

        my_query = "SELECT * FROM Event ORDER BY date desc"
        cursor.execute(my_query)
        events = []

        for (id, event_name, event_city, event_state, event_date, event_description) in cursor:
            event_info = {"id": id, "name": event_name, "date": event_date, "city": event_city, "state": event_state}
            events.append(event_info)

        print("hello3")

        if event_id=="None":
            error='Please select an event, if no events are displayed you may need to create a new event'
            return render_template('registerForRaceSelect.html', error=error, events=events)


        my_query = "SELECT * FROM Registered WHERE event="+event_id+" ORDER BY last_name, first_name"
        cursor.execute(my_query)
        registered_people = []

        for (id, first_name, last_name, bib, rfid_tag, event, gender, age, birthday) in cursor:
            people_info = {"id": id, "first_name": first_name, "last_name": last_name, "bib": bib}
            registered_people.append(people_info)

        my_query="SELECT name FROM Event WHERE id="+event_id
        cursor.execute(my_query)
        event_name=cursor.fetchone()[0]

        my_query="SELECT * FROM Race WHERE event="+event_id
        cursor.execute(my_query)
        races = []

        for(id, name, type, start_time, event, description) in cursor:
            race_info={"id": id, "name": name}
            races.append(race_info)

        return render_template('registerForRace.html', registered_people=registered_people, event_id=event_id, event_name=event_name, races=races)
    except Exception as e:
        error = 'Race registration could not be shown!'
        #return json.dumps({'error':str(e)}), 404
        return render_template('registerForRaceSelect.html', error=error, events=events)
       
@app.route("/registerForRace/<event_id>", methods=['POST', 'GET'])
def registerForRace(event_id=None):
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()

        print(event_id)

        person=request.form['person']
        signed_races=request.form.getlist('races')
        print(person)
        print(signed_races)

        my_query = "SELECT * FROM Registered WHERE event="+event_id+" ORDER BY last_name, first_name"
        cursor.execute(my_query)
        registered_people = []

        for (id, first_name, last_name, bib, rfid_tag, event, gender, age, birthday) in cursor:
            people_info = {"id": id, "first_name": first_name, "last_name": last_name, "bib": bib}
            registered_people.append(people_info)

        my_query="SELECT name FROM Event WHERE id="+event_id
        cursor.execute(my_query)
        event_name=cursor.fetchone()[0]

        my_query="SELECT * FROM Race WHERE event="+event_id
        cursor.execute(my_query)
        races = []

        for(id, name, type, start_time, event, description) in cursor:
            race_info={"id": id, "name": name}
            races.append(race_info)

        ################################## error checking ##########################################################
        
        print("about to check if fields filled out")

        #if all the required fields aren't filled out
        if (person == "None" or signed_races==[] or signed_races[0] == "None"):
            error = 'ALL of the required fields must be filled out!'
            return render_template('registerForRace.html', error=error, registered_people=registered_people, event_id=event_id, event_name=event_name, races=races)

        print("passed the checl")
        
        #if someone is already signed up with input bib number in this event
        success_races=""
        error_races=""
        error_triggered=0

        for arace in signed_races:
            print("this is the race:"+str(arace))
            my_query="SELECT COUNT(*) FROM Participant WHERE Participant.race="+str(arace)+" AND Participant.registration_id="+person
            cursor.execute(my_query)
            num_registered=cursor.fetchone()[0]

            print("now i'm gonna get the names")

            my_query="SELECT Registered.first_name, Registered.last_name, Race.name FROM Registered, Race WHERE Registered.id="+person+" AND Race.id="+str(arace)
            cursor.execute(my_query)
            names=cursor.fetchone()

            if arace != signed_races[0]:
                success_races+= " and "
            success_races+=names[2]

            if num_registered > 0:
                if arace != signed_races[0]:
                    error_races+=" and "
                error_races+=names[2]
                error_triggered=1
                
        #if theres an error
        if error_triggered==1:
            error=names[0]+" "+names[1]+" is already signed up for "+error_races+" in "+event_name
            return render_template('registerForRace.html', error=error, registered_people=registered_people, event_id=event_id, event_name=event_name, races=races)

        #################################### success and insert ##########################################################

        print("success races: "+success_races)

        for arace in signed_races:
            my_query = ("INSERT INTO Participant (race, registration_id) VALUES ('"+str(arace)+"','"+person+"')")
            print(my_query)
            cursor.execute(my_query)
            conn.commit()
        

        success = names[0]+" "+names[1]+" was signed up for "+success_races+" in "+event_name
        return render_template("registerForRace.html", success=success, registered_people=registered_people, event_id=event_id, event_name=event_name, races=races)
        
        
    except Exception as e:
        error = 'This person was not registered correctly!'
        return json.dumps({'error':str(e)}), 404
        #return render_template('registrationForm.html', error=error, registered_people=registered_people, event_id=event_id)
    finally:
        cursor.close()

@app.route("/deleteRace/<race_id>", methods=['POST', 'GET'])
def deleteRace(race_id=None):
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()
        cursor2 = conn.cursor()

        my_query="SELECT name, event FROM Race WHERE id="+str(race_id)
        cursor.execute(my_query)
        for (name, event) in cursor:
            race_name=name
            event_id=event

        #####FIRST GO DELETE ALL PARTICIPANT RACERS FOR THIS RACE
        my_query="DELETE FROM Participant WHERE race="+str(race_id)
        cursor.execute(my_query)

        #### THEN GO DELETE THE RACE
        my_query="DELETE FROM Race WHERE id="+str(race_id)
        cursor.execute(my_query)
        
        conn.commit()

        success=race_name+" was successfully deleted!"
        return redirect(url_for('showRaces', race_event=event_id, success=success))
    except Exception as e:
        error = 'Could not be properly deleted!'
        return json.dumps({'error':str(e)}), 404
        #return render_template('registrationForm.html', error=error, registered_people=registered_people, event_id=event_id, races=races)
    finally:
        cursor.close()

@app.route("/showEditRace/<race_id>", methods=['POST', 'GET'])
def showEditRace(race_id=None):
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()

        if 'error' in request.args:
            error = request.args['error']
        else:
            error="None"

        my_query = "SELECT * FROM Race WHERE id="+str(race_id)
        cursor.execute(my_query)
        for (id, name, type, start_time, event, description) in cursor:
            race_id=id
            race_name=name
            race_type=type
            race_start_time=start_time
            race_event=event
            race_description=description

        my_query="SELECT name FROM Event WHERE id="+str(race_event)
        cursor.execute(my_query)
        event_name=cursor.fetchone()[0]

        return render_template("editRace.html", race_id=race_id, race_name=race_name, race_type=race_type, race_start_time=race_start_time,
            race_event=race_event, race_description=race_description, event_name=event_name, error=error)
    except Exception as e:
        error = 'Could not be properly edited!'
        return json.dumps({'error':str(e)}), 404
        #return render_template('registrationForm.html', error=error, registered_people=registered_people, event_id=event_id, races=races)
    finally:
        cursor.close()

@app.route("/editRace/<race_id>", methods=['POST', 'GET'])
def editRace(race_id=None):
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()
        cursor2 = conn.cursor()

        race_name = request.form['race_name']
        race_type = request.form['race_type']
        race_start_time = request.form['race_start_time']
        race_description = request.form['race_description']

        print(race_name)

        my_query="SELECT Event.name FROM Event, Race WHERE Race.id="+str(race_id)+" AND Race.event=Event.id"
        print(my_query)
        cursor.execute(my_query)
        event_name=cursor.fetchone()[0]
        print(event_name)

        my_query = "SELECT * FROM Race WHERE id="+str(race_id)
        cursor.execute(my_query)
        for (id, name, type, start_time, event, description) in cursor:
            print(event)
            event_id=event
            my_query="SELECT * FROM Race WHERE name='"+race_name+"' AND event="+str(event)
            cursor2.execute(my_query)
            print(cursor2.rowcount)
            if cursor2.rowcount>0:
                print("error!")
                error="There is already a Race called '"+race_name+"' in "+event_name
                return redirect(url_for("showEditRace", race_id=race_id, error=error))

            if (race_name!=name or race_type!=type or race_start_time!=start_time or race_description!=description):
                my_query=("UPDATE Race SET name='"+race_name+"', type='"+race_type+"', start_time='"+race_start_time+"',"+
                    " description='"+race_description+"' WHERE id="+race_id)
                cursor.execute(my_query)
                conn.commit()

        success="Changes made to "+race_name+" successfully!"
        return redirect(url_for('showRaces', race_event=event_id, success=success))
    except Exception as e:
        error = 'Could not be properly edited!'
        return json.dumps({'error':str(e)}), 404
        #return render_template('registrationForm.html', error=error, registered_people=registered_people, event_id=event_id, races=races)
    finally:
        cursor.close()

###################################################### PARTICIPANT STUFF ################################################################

@app.route("/showParticipantForm")
def showParticipantForm():
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()

        my_query = "SELECT * FROM Race ORDER BY name"
        cursor.execute(my_query)
        races = []

        for (id, name, type, start_time, event, description) in cursor:
            race_info = {"id": id, "name": name}
            races.append(race_info)

        return render_template('participantForm.html', races=races)
    except Exception as e:
        error = 'Could not get participants properly'
        return render_template('participantForm.html', error=error)
    finally:
        cursor.close()

@app.route('/showParticipants/<participant_race>')
def showParticipants(participant_race=None):
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()

        if 'success' in request.args:
            success = request.args['success']
        else:
            success="None"

        if 'error' in request.args:
            error = request.args['error']
        else:
            error="None"

        my_query=("SELECT Event.name, Event.id, Event.city, Event.state, Event.date, Race.id, Race.name, Race.description FROM Event, Race WHERE Race.id="+
            participant_race+" AND Race.event=Event.id")
        cursor.execute(my_query)
        for(event_name, event_id, event_city, event_state, event_date, race_id, race_name, race_description) in cursor:
            e_name=event_name
            e_id=event_id
            e_city=event_city
            e_state=event_state
            e_date=event_date
            e_date = e_date.strftime('%m/%d/%Y')
            r_id=race_id
            r_name=race_name
            r_description=race_description

        my_query = ("SELECT Registered.*, Race.name, Race.id FROM Registered, Participant, Race WHERE Participant.race="+participant_race+
        " AND Participant.race=Race.id AND Registered.id=Participant.registration_id ORDER BY Registered.last_name, Registered.first_name, Race.name")
        print(my_query)
        participants = []

        cursor.execute(my_query)
        if cursor.rowcount == 0:
            print("no res")
            return render_template('participants.html', noResults="true", event=e_id, event_name=e_name, event_city=e_city, event_state=e_state,
            event_date=e_date, race_id=r_id, race_name=r_name, race_description=r_description, num_participants=cursor.rowcount, success=success,
            error=error)
        else:
            num_participants=cursor.rowcount

        print("made it")

        for (id, first_name, last_name, bib, rfid_tag, event, gender, age, license, phone, email, birthday, race_name, race_id) in cursor:
            print(first_name)
            print(last_name)
            print(bib)
            print(rfid_tag)
            print(event)
            print(gender)
            print(age)
            print(race_name)

            participant_info = {"id": id, "name": first_name+" "+last_name, "first_name": first_name, "last_name": last_name, "bib": bib, "rfid_tag": rfid_tag, 
            "gender": gender, "age": age, "license": license, "phone": phone, "email": email, "birthday": birthday, "race": race_name, "race_id": race_id}
            
            participants.append(participant_info)

        print("out of loop")

        return render_template('participants.html', participants=participants, event=e_id, event_name=e_name, event_city=e_city, event_state=e_state,
            event_date=e_date, race_id=r_id, race_name=r_name, race_description=r_description, num_participants=num_participants, success=success,
            error=error)

    except Exception as e:
        return json.dumps({'error':str(e)}), 404
    finally:
        cursor.close()

@app.route('/showAllParticipants/<event_id>')
def showAllParticipants(event_id=None):
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()

        if 'success' in request.args:
            success = request.args['success']
        else:
            success="None"
        print("in show all parts")

        my_query="SELECT name FROM Event WHERE id="+event_id
        cursor.execute(my_query)
        event_name=cursor.fetchone()[0]

        my_query = "SELECT * FROM Registered WHERE Registered.event="+event_id+" ORDER BY Registered.last_name, Registered.first_name"
        print(my_query)
        participants = []

        cursor.execute(my_query)
        if cursor.rowcount == 0:
            print("no res")
            return render_template('participants.html', noResults="true", event=event_id, event_name=event_name, allParticipants="true", 
                success=success, num_participants=0)
        else:
            num_participants=cursor.rowcount

        for (id, first_name, last_name, bib, rfid_tag, event, gender, age, licesne, phone, email, birthday) in cursor:
            participant_info = {"id": id, "name": first_name+" "+last_name, "first_name": first_name, "last_name": last_name, "bib": bib, "rfid_tag": rfid_tag, 
            "gender": gender, "age": age, "license": license, "phone": phone, "email": email, "birthday": birthday}
            
            participants.append(participant_info)

        return render_template('participants.html', participants=participants, event=event_id, event_name=event_name, allParticipants="true", 
            success=success, num_participants=num_participants)

    except Exception as e:
        return json.dumps({'error':str(e)}), 404
    finally:
        cursor.close()

@app.route("/deleteRaceParticipant/<participant_race>/<participant_id>", methods=['POST', 'GET'])
def deleteRaceParticipant(participant_race=None, participant_id=None):
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()
        cursor2 = conn.cursor()

        my_query = "SELECT * FROM Registered WHERE id="+str(participant_id)
        cursor.execute(my_query)
        for(id, first_name, last_name, bib, rfid_tag, event, gender, age, license, phone, email, birthday) in cursor:
            participant_name=first_name+" "+last_name

        #####FIRST GO DELETE THE SPECIFIED PARTICIPANT OF THIS RACE
        my_query="DELETE FROM Participant WHERE race="+str(participant_race)+" AND registration_id="+str(participant_id)
        cursor.execute(my_query)
        
        conn.commit()

        success=participant_name+" was successfully deleted!"
        return redirect(url_for('showParticipants', participant_race=participant_race, success=success))
    except Exception as e:
        error = 'Could not be properly deleted!'
        return json.dumps({'error':str(e)}), 404
        #return render_template('registrationForm.html', error=error, registered_people=registered_people, event_id=event_id, races=races)
    finally:
        cursor.close()

@app.route("/showEditRaceParticipant/<participant_race>/<participant_id>", methods=['POST', 'GET'])
def showEditRaceParticipant(participant_race=None, participant_id=None):
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()

        if 'error' in request.args:
            error = request.args['error']
        else:
            error="None"

        my_query = "SELECT * FROM Registered WHERE id="+str(participant_id)
        cursor.execute(my_query)
        for (id, first_name, last_name, bib, rfid_tag, event, gender, age, license, phone, email, birthday) in cursor:
            participant_stuff = {"id": id, "name": first_name+" "+last_name, "first_name": first_name, "last_name": last_name, "bib": bib, "rfid_tag": rfid_tag, 
            "gender": gender, "age": age, "license": license, "phone": phone, "email": email, "birthday": birthday}

        my_query="SELECT * FROM Race WHERE id="+str(participant_race)
        cursor.execute(my_query)
        for(id, name, type, start_time, event, description) in cursor:
            participant_stuff['race_id']=id
            participant_stuff['race_name']=name
            participant_stuff['event_id']=event

        my_query="SELECT name FROM Event WHERE id="+str(participant_stuff['event_id'])
        cursor.execute(my_query)
        participant_stuff['event_name']=cursor.fetchone()[0]

        return render_template("editRaceParticipant.html", participant=participant_stuff, error=error)
    except Exception as e:
        error = 'Could not be properly edited!'
        return json.dumps({'error':str(e)}), 404
        #return render_template('registrationForm.html', error=error, registered_people=registered_people, event_id=event_id, races=races)
    finally:
        cursor.close()

@app.route("/editRaceParticipant/<participant_race>/<participant_id>", methods=['POST', 'GET'])
def editRaceParticipant(participant_race=None, participant_id=None):
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()

        p_first_name = request.form['first_name']
        p_last_name = request.form['last_name']
        p_bib = request.form['bib']
        p_rfid_tag = request.form['rfid_tag']
        p_gender = request.form['gender']
        p_birthday = request.form['birthday']
        if p_birthday=="":
            print("wtf")
            error="This person must have all information filled out, don't leave anything blank!"
            return redirect(url_for('showEditRaceParticipant', participant_race=participant_race, participant_id=participant_id, error=error))
        else:
            print(p_birthday)

        my_query="SELECT date FROM Event, Race WHERE Event.id=Race.event AND Race.id="+str(participant_race)
        cursor.execute(my_query)
        event_date=cursor.fetchone()[0]

        bday_year = datetime.strptime(p_birthday, '%Y-%m-%d')
        bday_year=bday_year.strftime('%Y')
        event_year = event_date.strftime('%Y')
        p_age=str(calc_age(bday_year, event_year))

        p_license = request.form['license']
        p_phone = request.form['phone']
        p_email = request.form['email']

        if p_first_name=="" or p_last_name=="" or p_bib=="" or p_rfid_tag=="" or p_gender=="" or p_license=="" or p_phone=="" or p_email=="":
            error="This person must have all information filled out, don't leave anything blank!"
            return redirect(url_for('showEditRaceParticipant', participant_race=participant_race, participant_id=participant_id, error=error))

        # CALCULATE P_AGE !!!11

        my_query="SELECT race FROM Participant WHERE "

        my_query = "SELECT * FROM Registered WHERE id="+str(participant_id)
        cursor.execute(my_query)
        for (id, first_name, last_name, bib, rfid_tag, event, gender, age, license, phone, email, birthday) in cursor:
            if (p_first_name!=first_name or p_last_name!=last_name or p_bib!=bib or p_rfid_tag!=rfid_tag or p_gender!=gender or p_age!=age 
                or p_license!=license or p_phone!=phone or p_email!=email or p_birthday!=p_birthday):
                my_query=("UPDATE Registered SET first_name='"+p_first_name+"', last_name='"+p_last_name+"', bib='"+p_bib+"',"+
                    " rfid_tag='"+p_rfid_tag+"', gender='"+p_gender+"', age='"+p_age+"', license='"+p_license+"', phone='"+p_phone+
                    "', email='"+p_email+"', birthday='"+p_birthday+"' WHERE id="+participant_id)
                cursor.execute(my_query)
                conn.commit()

        success="Changes made to "+p_first_name+" "+p_last_name+" successfully!"
        return redirect(url_for('showParticipants', participant_race=participant_race, success=success))
    except Exception as e:
        error = 'Could not be properly edited!'
        return json.dumps({'error':str(e)}), 404
        #return render_template('registrationForm.html', error=error, registered_people=registered_people, event_id=event_id, races=races)
    finally:
        cursor.close()

##########SAME THING BUT MESS WITH THE REGISTERED PEOPLE INSTEAD OF JUST PARTICIPANTS IN A RACE#############

@app.route("/deleteRegistered/<participant_id>", methods=['POST', 'GET'])
def deleteRegistered(participant_id=None):
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()
        cursor2 = conn.cursor()

        my_query = "SELECT * FROM Registered WHERE id="+str(participant_id)
        cursor.execute(my_query)
        for(id, first_name, last_name, bib, rfid_tag, event, gender, age, license, phone, email, birthday) in cursor:
            participant_name=first_name+" "+last_name
            event_id=event

        #####FIRST GO DELETE THE SPECIFIED PARTICIPANT IN ALL RACES HE/SHE IS REGISTERED IN
        my_query="DELETE FROM Participant WHERE registration_id="+str(participant_id)
        cursor.execute(my_query)
        

        ##### THEN GO DELETE THEIR ACTUAL REGISTRATION IN THE EVENT
        my_query="DELETE FROM Registered WHERE id="+str(participant_id)
        cursor.execute(my_query)
        conn.commit()

        success=participant_name+" was successfully deleted!"
        return redirect(url_for('showAllParticipants', event_id=event_id, success=success))
    except Exception as e:
        error = 'Could not be properly deleted!'
        return json.dumps({'error':str(e)}), 404
        #return render_template('registrationForm.html', error=error, registered_people=registered_people, event_id=event_id, races=races)
    finally:
        cursor.close()

@app.route("/showEditRegistered/<participant_id>", methods=['POST', 'GET'])
def showEditRegistered(participant_id=None):
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()

        if 'error' in request.args:
            error = request.args['error']
        else:
            error="None"

        my_query = "SELECT * FROM Registered WHERE id="+str(participant_id)
        cursor.execute(my_query)
        for (id, first_name, last_name, bib, rfid_tag, event, gender, age, license, phone, email, birthday) in cursor:
            participant_stuff = {"id": id, "name": first_name+" "+last_name, "first_name": first_name, "last_name": last_name, "bib": bib, "rfid_tag": rfid_tag, 
            "event_id": event, "gender": gender, "age": age, "license": license, "phone": phone, "email": email, "birthday": birthday}

        my_query="SELECT name FROM Event WHERE id="+str(participant_stuff['event_id'])
        cursor.execute(my_query)
        participant_stuff['event_name']=cursor.fetchone()[0]

        return render_template("editRaceParticipant.html", participant=participant_stuff, error=error)
    except Exception as e:
        error = 'Could not be properly edited!'
        return json.dumps({'error':str(e)}), 404
        #return render_template('registrationForm.html', error=error, registered_people=registered_people, event_id=event_id, races=races)
    finally:
        cursor.close()

@app.route("/editRegistered/<participant_id>", methods=['POST', 'GET'])
def editRegistered(participant_id=None):
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()
        
        p_first_name = request.form['first_name']
        p_last_name = request.form['last_name']
        p_bib = request.form['bib']
        p_rfid_tag = request.form['rfid_tag']
        p_gender = request.form['gender']
        p_birthday = request.form['birthday']
        if p_birthday=="":
            error="This person must have all information filled out, don't leave anything blank!"
            return redirect(url_for('showEditRegistered', participant_id=participant_id, error=error))

        my_query="SELECT date FROM Event, Registered WHERE Event.id=Registered.event AND Registered.id="+str(participant_id)
        cursor.execute(my_query)
        event_date=cursor.fetchone()[0]

        bday_year = datetime.strptime(p_birthday, '%Y-%m-%d')
        bday_year=bday_year.strftime('%Y')
        event_year = event_date.strftime('%Y')
        p_age=str(calc_age(bday_year, event_year))

        p_license = request.form['license']
        p_phone = request.form['phone']
        p_email = request.form['email']

        if p_first_name=="" or p_last_name=="" or p_bib=="" or p_rfid_tag=="" or p_gender=="" or p_license=="" or p_phone=="" or p_email=="":
            error="This person must have all information filled out, don't leave anything blank!"
            return redirect(url_for('showEditRegistered', participant_id=participant_id, error=error))

        # CALCULATE P_AGE !!!!

        print("hello!")

        my_query = "SELECT * FROM Registered WHERE id="+str(participant_id)
        cursor.execute(my_query)
        for (id, first_name, last_name, bib, rfid_tag, event, gender, age, license, phone, email, birthday) in cursor:
            event_id=event
            if (p_first_name!=first_name or p_last_name!=last_name or p_bib!=bib or p_rfid_tag!=rfid_tag or p_gender!=gender or p_age!=age or
                p_license!=license or p_phone!=phone or p_email!=email or p_birthday!=p_birthday):
                my_query=("UPDATE Registered SET first_name='"+p_first_name+"', last_name='"+p_last_name+"', bib='"+p_bib+"',"+
                    " rfid_tag='"+p_rfid_tag+"', gender='"+p_gender+"', age='"+p_age+"', license='"+p_license+"', phone='"+p_phone+
                    "', email='"+p_email+"', birthday='"+p_birthday+"' WHERE id="+participant_id)
                cursor.execute(my_query)
                conn.commit()
                print("just committed")

        success="Changes made to "+p_first_name+" "+p_last_name+" successfully!"
        print(success)
        return redirect(url_for('showAllParticipants', event_id=event_id, success=success))
    except Exception as e:
        error = 'Could not be properly edited!'
        return json.dumps({'error':str(e)}), 404
        #return render_template('registrationForm.html', error=error, registered_people=registered_people, event_id=event_id, races=races)
    finally:
        cursor.close()

############# INDIVIDUAL STUFF ###################

@app.route('/showIndividual/<participant_id>/<participant_race>')
def showIndividual(participant_id=None, participant_race=None):
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()

        if 'success' in request.args:
            success = request.args['success']
        else:
            success="None"

        races = []
        my_query=("SELECT Event.name, Race.* FROM Event, Race, Participant WHERE Event.id=Race.event AND Participant.race=Race.id "+
        "AND Participant.registration_id="+str(participant_id))
        cursor.execute(my_query)
        for(event_name1, id, name, type, start_time, event, description) in cursor:
            event_name=event_name1
            print(name)
            print(id)
            race_stuff = {"id": id, "name": name, "type": type, "start_time": start_time, "event": event, "description": description}
            races.append(race_stuff)

        my_query="SELECT * FROM Race WHERE Race.id="+str(participant_race)
        cursor.execute(my_query)
        for(id, name, type, start_time, event, description) in cursor:
            race_name=name
            race_id=id
            event_id=event

        my_query = "SELECT * FROM Registered WHERE id="+str(participant_id)
        cursor.execute(my_query)
        if cursor.rowcount == 0:
            print("no res")
            return render_template('individual.html', noResults="true", races=races, success=success, event_name=event_name, event_id=event_id, 
                race_name=race_name, race_id=race_id)
        else:
            num_participants=cursor.rowcount

        print("made it")

        for (id, first_name, last_name, bib, rfid_tag, event, gender, age, license, phone, email, birthday) in cursor:
            birthday = birthday.strftime('%m/%d/%Y')
            individual = {"id": id, "name": first_name+" "+last_name, "first_name": first_name, "last_name": last_name, "bib": bib, "rfid_tag": rfid_tag, 
            "gender": gender, "age": age, "license": license, "phone": phone, "email": email, "birthday": birthday}

        print("out of loop")

        return render_template('individual.html', individual=individual, races=races, num_participants=num_participants, success=success, 
            event_id=event_id, event_name=event_name, race_name=race_name, race_id=race_id)

    except Exception as e:
        return json.dumps({'error':str(e)}), 404
    finally:
        cursor.close()

@app.route('/showAllIndividual/<participant_id>/<event_id>')
def showAllIndividual(participant_id=None, event_id=None):
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()

        if 'success' in request.args:
            success = request.args['success']
        else:
            success="None"

        races = []
        my_query=("SELECT Event.name, Race.* FROM Event, Race, Participant WHERE Event.id=Race.event AND Participant.race=Race.id "+
        "AND Participant.registration_id="+str(participant_id))
        cursor.execute(my_query)
        for(event_name1, id, name, type, start_time, event, description) in cursor:
            event_name=event_name1
            race_stuff = {"id": id, "name": name, "type": type, "start_time": start_time, "event": event, "description": description}
            races.append(race_stuff)

        my_query = "SELECT * FROM Registered WHERE id="+str(participant_id)
        cursor.execute(my_query)
        if cursor.rowcount == 0:
            print("no res")
            return render_template('individual.html', noResults="true", races=races, success=success, event_name=event_name, event_id=event_id)
        else:
            num_participants=cursor.rowcount

        print("made it")

        for (id, first_name, last_name, bib, rfid_tag, event, gender, age, license, phone, email, birthday) in cursor:
            birthday = birthday.strftime('%m/%d/%Y')
            individual = {"id": id, "name": first_name+" "+last_name, "first_name": first_name, "last_name": last_name, "bib": bib, "rfid_tag": rfid_tag, 
            "gender": gender, "age": age, "license": license, "phone": phone, "email": email, "birthday": birthday}

        print("out of loop")

        return render_template('individual.html', individual=individual, races=races, num_participants=num_participants, success=success, 
            event_id=event_id, event_name=event_name)

    except Exception as e:
        return json.dumps({'error':str(e)}), 404
    finally:
        cursor.close()

###################################################### UPLOAD STUFF ################################################################

@app.route('/showUploadSelect') #show all races in dropdown on event select screen for uploading a file
def showUploadSelect():
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()

        my_query = "SELECT * FROM Event ORDER BY date desc"
        cursor.execute(my_query)
        events = []

        print("hello")

        for (id, event_name, event_city, event_state, event_date, event_description) in cursor:
            event_info = {"id": id, "name": event_name, "date": event_date, "city": event_city, "state": event_state}
            events.append(event_info)

        return render_template('uploadSelect.html', events=events)
    except Exception as e:
        error = 'Could not get events properly'
        return render_template('uploadSelect.html', error=error)
    finally:
        cursor.close()

@app.route("/showUpload", methods=['POST', 'GET'])
def showUpload():
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()
        event_id=request.form['event']
        print(event_id)
        if event_id=="None":
            error="You need to select an event!"
            return render_template('uploadSelect.html')

        my_query="SELECT name FROM Event WHERE id="+event_id
        cursor.execute(my_query)
        event_name=cursor.fetchone()[0]

        my_query="SELECT name, id FROM Race WHERE event="+event_id
        cursor.execute(my_query)
        races = []
        for (name, id) in cursor:
            race_info = {"id": id, "name": name}
            races.append(race_info)

        print("hello again")

        return render_template('upload.html', event_id=event_id, event_name=event_name, races=races)
    except Exception as e:
        error = 'Could not get that event'
        return render_template('uploadSelect.html', error=error)
    finally:
        cursor.close()

@app.route("/upload/<event_id>", methods=['GET', 'POST'])
def upload(event_id=None):
    file = request.files['fileInput']
    print(file)
    # Check if the file is one of the allowed types/extensions
    if file and allowed_file(file.filename):
        # Make the filename safe, remove unsupported chars
        filename = secure_filename(file.filename)
        # Move the file form the temporal folder to
        # the upload folder we setup
        file.save(filename)
        # Redirect the user to the uploaded_file route, which
        # will basicaly show on the browser the uploaded file
        return redirect(url_for('read_file', filename=filename, event_id=event_id))

@app.route('/read_file')
def read_file():
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()

        filename = request.args['filename']
        event_id = request.args['event_id']
        
        my_query="SELECT name FROM Event WHERE id="+event_id
        cursor.execute(my_query)
        event_name=cursor.fetchone()[0]

        my_query="SELECT name, id FROM Race WHERE event="+event_id
        cursor.execute(my_query)
        races = []
        for (name, id) in cursor:
            race_info = {"id": id, "name": name}
            races.append(race_info)

        print(races)

        if os.path.isfile(filename) == False:
            error="Failed to upload file, file format incorrect. One or more lines were not added from file"
            return(render_template('upload.html',error=error))

        with open(filename, "rU") as file:
            reader = csv.reader(file, delimiter="\t")
            registered_already = []
            events_for_person = []
            print("The event id is: ", event_id)
            for i, line in enumerate(reader):
                contents=line[0].split(",")
                print(contents)
                print(len(contents))
                if i>0:
                    print("in >0: ", i)
                    first_name=contents[0].replace("'","''")
                    last_name=contents[1].replace("'","''")
                    license=contents[2]
                    bib=contents[3]
                    rfid_tag=contents[4]
                    gender=contents[5]
                    birthday=contents[6]

                    my_query="SELECT date FROM Event WHERE id="+event_id
                    cursor.execute(my_query)
                    event_date=cursor.fetchone()[0]

                    bday_year = datetime.strptime(birthday, '%m/%d/%Y')
                    bday_year=bday_year.strftime('%Y')
                    event_year = event_date.strftime('%Y')
                    age=str(calc_age(bday_year, event_year))

                    # CALCULATE AGE HERE
                    phone=contents[7]
                    email=contents[8]

                    events_for_person[:] = []

                    for j in contents[9:]:
                        if j != "":
                            events_for_person.append(j)

                    print("events: ", events_for_person)

                    #####This is the Registered Person info
                    my_query=("SELECT id FROM Registered WHERE bib='"+str(bib)+"' AND event='"+str(event_id)+"' OR rfid_tag='"+str(rfid_tag)+
                        "' AND event='"+str(event_id)+"' OR license='"+str(license)+"' AND event='"+str(event_id)+"'")
                    print(my_query)
                    cursor.execute(my_query)
                    if cursor.rowcount>0:
                        ######This PERSON is already REGISTERED!
                        person_exists=1
                        person_info={"id":cursor.fetchone()[0], "first_name": first_name, "last_name": last_name, "bib": str(bib), 
                        "rfid_tag": str(rfid_tag), "license": str(license)} #REGISTERED ALREADY
                        registered_already.append(person_info)
                        print("NAME: ", first_name, last_name)
                    else:
                        ##### GO ahead and insert now
                        my_query=("INSERT INTO Registered (first_name, last_name, bib, rfid_tag, event, gender, age, license, phone, email, birthday) VALUES ('"+
                            first_name+"','"+last_name+"','"+str(bib)+"','"+str(rfid_tag)+"','"+str(event_id)+"','"+gender+"','"+str(age)+"','"+
                            str(license)+"','"+str(phone)+"','"+str(email)+"','"+str(birthday)+"')")
                        print(my_query)
                        cursor.execute(my_query)
                        conn.commit()
        ##### ALL DONE
        file.close()
        success="Successful Upload!"
        print(registered_already)
        return render_template('upload.html', success=success, registered_already=registered_already, event_id=event_id, event_name=event_name, races=races)
    except Exception as e:
        error = 'Could not get participants properly'
        return json.dumps({'error':str(e)}), 404
    finally:
        cursor.close()

@app.route('/downloadExample')
def downloadExample():
    csv = """"firstname","lastname","license","bib","rfid_tag","gender","birthday (mm/dd/yyyy)","phone","email","race_id1","race_id2","race_id3","etc"""
    # We need to modify the response, so the first thing we 
    # need to do is create a response out of the CSV string
    response = make_response(csv)
    # This is the key: Set the right header for the response
    # to be downloaded, instead of just printed on the browser
    response.headers["Content-Disposition"] = "attachment; filename=format.csv"
    return response

# CREATE A DELETE FILE THING LATER

########################################################## SEARCHING ################################################################

@app.route("/searchEvents", methods=['GET', 'POST'])
def searchEvents():
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()
        cursor2 = conn.cursor()

        print("searched")

        my_query = "SELECT * FROM Event ORDER BY date desc, name"
        events = []
        cursor.execute(my_query)
        for (id, event_name, event_city, event_state, event_date, event_description) in cursor:
            event_date = event_date.strftime('%m/%d/%Y')
            event_info = {"id": id, "name": event_name, "city": event_city, "state": event_state, "date": event_date, "description": event_description}
            events.append(event_info)

        print("about to search")

        search_string = request.form['search_string']
        print(search_string)

        if search_string == "":
            error = 'You must type in at least one character!'
            return render_template('events.html', error=error, events=events)

        my_query=("SELECT DISTINCT * FROM Event WHERE name LIKE'%"+search_string+"%' ORDER BY CASE WHEN name='"+search_string+
            "' THEN 0 WHEN name LIKE '"+search_string+"%' THEN 1 WHEN name LIKE '%"+search_string+"%' THEN 2 WHEN name LIKE '%"+search_string+
            "' THEN 3 ELSE 4 END, name ASC")
        search_results = []
        cursor.execute(my_query)
        for (id, event_name, event_city, event_state, event_date, event_description) in cursor:
            my_query2="SELECT COUNT(*) FROM Race WHERE event="+str(id)
            cursor2.execute(my_query2)
            race_count=cursor2.fetchone()[0]

            my_query2="SELECT COUNT(*) FROM Registered WHERE event="+str(id)
            cursor2.execute(my_query2)
            registered_racers=cursor2.fetchone()[0]

            event_date = event_date.strftime('%m/%d/%Y')
            event_info = {"id": id, "name": event_name, "city": event_city, "state": event_state, "date": event_date, "description": event_description, "race_count": race_count, "registered_racers": registered_racers}
            search_results.append(event_info)

        success = "The Race was successfully created!"
        return render_template("searchEvents.html", success=success, search_results=search_results, search_string=search_string)
    except Exception as e:
        error = 'This Race was not properly created!'
        return json.dumps({'error':str(e)}), 404
        #return render_template('raceForm.html', error=error, events=events)
    finally:
        cursor.close()

@app.route("/searchRaces/<event_id>", methods=['GET', 'POST'])
def searchRaces(event_id=None):
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()
        cursor2 = conn.cursor()

        search_string = request.form['search_string']

        if search_string == "":
            error = 'You must type in at least one character!'
            return redirect(url_for('showRaces', event_id=event_id, error=error))

        my_query="SELECT name, date, city, state FROM Event WHERE id="+str(event_id)
        cursor.execute(my_query)
        for(name, date, city, state) in cursor:
            event_name=name
            event_date=date
            event_date = event_date.strftime('%m/%d/%Y')
            event_city=city
            event_state=state

        my_query=("SELECT DISTINCT * FROM Race WHERE event="+event_id+" AND name LIKE'%"+search_string+"%' ORDER BY CASE WHEN name='"+search_string+
            "' THEN 0 WHEN name LIKE '"+search_string+"%' THEN 1 WHEN name LIKE '%"+search_string+"%' THEN 2 WHEN name LIKE '%"+search_string+
            "' THEN 3 ELSE 4 END, name ASC")
        search_results = []
        cursor.execute(my_query)
        for (id, name, type, start_time, event, description) in cursor:
            my_query2="SELECT COUNT(*) FROM Participant WHERE race="+str(id)
            cursor2.execute(my_query2)
            participant_count=cursor2.fetchone()[0]

            race_info = {"id": id, "name": name, "type": type, "start_time": start_time, "city": event_city, "state": event_state, 
            "date": event_date, "description": description, "participant_count": participant_count}
            search_results.append(race_info)

        print(search_results)

        return render_template("searchRaces.html", search_results=search_results, search_string=search_string, event_id=event_id, event_name=event_name)
    except Exception as e:
        error = 'This Race was not properly created!'
        return json.dumps({'error':str(e)}), 404
        #return render_template('raceForm.html', error=error, events=events)
    finally:
        cursor.close()

@app.route("/searchEverything", methods=['GET', 'POST'])
def searchEverything():
    try:
        conn = mysql.get_db()
        cursor = conn.cursor()
        cursor2 = conn.cursor()

        search_string = request.form['search_string']

        if search_string == "":
            error = 'You must type in at least one character!'
            return redirect(url_for('main', race_id=race_id, error=error))

        my_query="SELECT name, event FROM Race WHERE id="+str(race_id)
        cursor.execute(my_query)
        for(name, event) in cursor:
            race_name=name
            event_id=event

        my_query="SELECT name, date, city, state FROM Event WHERE id="+str(event_id)
        cursor.execute(my_query)
        for(name, date, city, state) in cursor:
            event_name=name
            event_date=date
            event_date = event_date.strftime('%m/%d/%Y')
            event_city=city
            event_state=state

        my_query=("SELECT DISTINCT * FROM Participant WHERE race="+race_id+" AND first_name LIKE'%"+search_string+"%' ORDER BY CASE WHEN name='"+search_string+
            "' THEN 0 WHEN name LIKE '"+search_string+"%' THEN 1 WHEN name LIKE '%"+search_string+"%' THEN 2 WHEN name LIKE '%"+search_string+
            "' THEN 3 ELSE 4 END, name ASC")
        search_results = []
        cursor.execute(my_query)
        for (id, name, type, start_time, event, description) in cursor:
            my_query2="SELECT COUNT(*) FROM Participant WHERE race="+str(id)
            cursor2.execute(my_query2)
            participant_count=cursor2.fetchone()[0]

            race_info = {"id": id, "name": name, "type": type, "start_time": start_time, "city": event_city, "state": event_state, 
            "date": event_date, "description": description, "participant_count": participant_count}
            search_results.append(race_info)

        print(search_results)

        return render_template("searchRaces.html", search_results=search_results, search_string=search_string, event_id=event_id, event_name=event_name)
    except Exception as e:
        error = 'This Race was not properly created!'
        return json.dumps({'error':str(e)}), 404
        #return render_template('raceForm.html', error=error, events=events)
    finally:
        cursor.close()


######################### Functions ##########
#############################################






@app.route("/participantForm", methods=['POST', 'GET'])
def participantForm():
    conn = mysql.get_db()
    cursor = conn.cursor()

    my_query = "SELECT * FROM Race ORDER BY name"
    cursor.execute(my_query)
    races = []

    for (id, name, type, start_time, event, description) in cursor:
        race_info = {"id": id, "name": name}
        races.append(race_info)

    try:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        bib = request.form['bib']
        rfid_tag = request.form['rfid_tag']
        gender = request.form['gender']
        age = request.form['age']
        race = request.form['race']

        print(race) 

        if (first_name == "" or last_name == "" or bib == "" or rfid_tag == "" or gender == "" or age == "0" or race == ""):
            error = 'ALL of the required fields must be filled out!'
            return render_template('participantForm.html', error=error, races=races)

        my_query = ("INSERT INTO Participant (first_name, last_name, bib, rfid_tag, gender, age, race) VALUES ('"+first_name+"','"+last_name+"','"+
            bib+"','"+rfid_tag+"','"+gender+"','"+age+"','"+race+"')")

        print(my_query)
        
        cursor.execute(my_query)
        conn.commit()

        success = "The Participant was successfully created!"
        return render_template("participantForm.html", success=success, races=races)
    except Exception as e:
        error = 'This Participant was not properly created!'
        return render_template('participantForm.html', error=error, races=races)
    finally:
        cursor.close()

if __name__=="__main__":
    app.secret_key = os.urandom(12)
    app.run()


