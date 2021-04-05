import datetime
from flask import Flask, render_template,session
from google.cloud import datastore
import google.oauth2.id_token
from flask import Flask, render_template, request,redirect
from google.auth.transport import requests
from datetime import timedelta
from datetime import datetime
import local_constants
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "jawad1.json"

app = Flask(__name__)
app.secret_key = 'assignment2'
datastore_client = datastore.Client()
firebase_request_adapter = requests.Request()

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=60)

def createUserInfo(claims):
    user_id = random.getrandbits(63)
    entity_key = datastore_client.key('UserInfoForAssignment3', user_id)
    entity = datastore.Entity(key = entity_key)
    entity.update({
    'email': claims['email'],
    'name': claims['name'],
    'root_directory': user_id+"/"
    })
    datastore_client.put(entity)

def retrieveUserInfo(claims):
    query = datastore_client.query(kind = 'UserInfoForAssignment3')
    query.add_filter('email','=',claims['email'])
    return query.fetch()

@app.route('/',methods = ['POST', 'GET'])
def root():
    if request.method == 'POST':
        return render_template('index.html', error_message=error_message)
    else:
        id_token = request.cookies.get("token")
        error_message = None
        rooms_list = None
        if id_token:
            try:
                claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
                session['name'] = claims['name']
                session['email'] = claims['email']
            except ValueError as exc:
                error_message = str(exc)
        else:
            session['name'] = None
            session['email'] = None
        return render_template('index.html', error_message=error_message)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
