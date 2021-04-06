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
app.secret_key = 'assignment3'
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

def retrieveUserInfo(email):
    entity_key = datastore_client.key('UserInfoForAssignment3', email)
    entity = datastore_client.get(entity_key)
    return entity

def blobList(prefix):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    return storage_client.list_blobs(local_constants.PROJECT_STORAGE_BUCKET, prefix=prefix)

def check_existance_of_directory(path,dir_name,cur_user):
    dir_list = cur_user['directory_list']
    for d in dir_list:
        directory_key = datastore_client.key('DirectoryInfo', d.name)
        dir_data = datastore_client.get(directory_key)
        if dir_data['directory_path'] == path and dir_data['directory_name'] == dir_name:
            return True
        print(d.name)
    return False