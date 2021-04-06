import datetime
from flask import Flask, render_template,session
from google.cloud import datastore,storage
import google.oauth2.id_token
from flask import Flask, render_template, request,redirect
from google.auth.transport import requests
from datetime import timedelta
from datetime import datetime
import local_constants
import random
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
    root_directory_id = random.getrandbits(63)
    entity_key = datastore_client.key('UserInfoForAssignment3', claims['email'])
    entity = datastore.Entity(key = entity_key)
    entity.update({
        'email': claims['email'],
        'name': claims['name'],
        'root_directory': str(root_directory_id),
        'directory_list': [],
        'file_list':[]
    })
    datastore_client.put(entity)
    return root_directory_id

def create_directory_in_cloud_storage(root_directory,path,directory_name):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(root_directory+path+directory_name)
    blob.upload_from_string('', content_type='application/x-www-form-urlencoded;charset=UTF-8')

def create_directory_in_datastore(directory_name,path):
    entity_key = datastore_client.key('UserInfoForAssignment3', session['email'])
    cur_user = datastore_client.get(entity_key)
    directory_key = datastore_client.key('DirectoryInfo', directory_name)
    entity = datastore.Entity(key = directory_key)
    entity.update({
        'directory_name': directory_name,
        'directory_path': path
    })
    datastore_client.put(entity)
    directory_list = cur_user['directory_list']
    directory_list.append(directory_key)
    cur_user.update({
        'directory_list':directory_list
    })
    datastore_client.put(cur_user)

def create_file_in_datastore(file_name,path,is_shared):
    entity_key = datastore_client.key('UserInfoForAssignment3', session['email'])
    cur_user = datastore_client.get(entity_key)
    file_key = datastore_client.key('fileInfo', file_name)
    entity = datastore.Entity(key = file_key)
    entity.update({
        'file_name': file_name,
        'file_path': path,
        'is_file_shared': is_shared
    })
    datastore_client.put(entity)
    file_list = cur_user['file_list']
    file_list.append(file_key)
    cur_user.update({
        'file_list':file_list
    })
    datastore_client.put(cur_user)

def create_file_in_cloud_storage(file,path,root_directory):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(root_directory+path+file.filename)
    blob.upload_from_file(file)

def retrieveUserInfo(claims):
    entity_key = datastore_client.key('UserInfoForAssignment3', claims['email'])
    entity = datastore_client.get(entity_key)
    return entity

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
                user_info = retrieveUserInfo(claims)
                if user_info == None:
                    root_directory_id = createUserInfo(claims)
                    create_directory_in_cloud_storage("","",str(root_directory_id)+"/")
                user_info = retrieveUserInfo(claims)
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
