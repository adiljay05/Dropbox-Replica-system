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
    dir_id = random.getrandbits(63)
    directory_key = datastore_client.key('DirectoryInfo', dir_id)
    entity = datastore.Entity(key = directory_key)
    entity.update({
        'directory_name': directory_name,
        'directory_path': path
    })
    datastore_client.put(entity)
    directory_list = cur_user['directory_list']
    directory_list.append(dir_id)
    cur_user.update({
        'directory_list':directory_list
    })
    datastore_client.put(cur_user)

def create_file_in_datastore(file_name,path,is_shared):
    entity_key = datastore_client.key('UserInfoForAssignment3', session['email'])
    cur_user = datastore_client.get(entity_key)
    file_id = random.getrandbits(63)
    file_key = datastore_client.key('fileInfo', file_id)
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
        directory_key = datastore_client.key('DirectoryInfo', d)
        dir_data = datastore_client.get(directory_key)
        if dir_data['directory_path'] == path and dir_data['directory_name'] == dir_name:
            return True
    return False

def get_root_directory(email):
    entity_key = datastore_client.key('UserInfoForAssignment3', email)
    cur_user = datastore_client.get(entity_key)
    return cur_user['root_directory']

def get_directories_from_datastore():
    cur_user = retrieveUserInfo(session['email'])
    directory_list = cur_user['directory_list']
    dir_list = []
    for d in directory_list:
        # print(d)
        directory_key = datastore_client.key('DirectoryInfo', int(d))
        dir_list.append(datastore_client.get(directory_key))
    return dir_list

def get_files_from_datastore():
    cur_user = retrieveUserInfo(session['email'])
    files_list = cur_user['file_list']
    file_list = []
    for f in files_list:
        file_key = datastore_client.key('FileInfo', int(f))
        file_list.append(datastore_client.get(file_key))
    return file_list

def get_directories_from_datastore_(path):
    cur_user = retrieveUserInfo(session['email'])
    directory_list = cur_user['directory_list']
    dir_list = []
    for d in directory_list:
        # print(d)
        directory_key = datastore_client.key('DirectoryInfo', int(d))
        dir_ = datastore_client.get(directory_key)
        if path == dir_['directory_path']:
            print(dir_['directory_name'])
            dir_list.append(dir_)
    return dir_list
    


def get_files_and_directories_at_current_path(path):
    directory_list = []
    file_list = []
    blob_list = blobList(path)
    for i in blob_list:
        if i.name[len(i.name) - 1] == '/':
            directory_list.append(i)
        else:
            file_list.append(i)
    return [directory_list,file_list]

def delete_directory_or_file_from_cloud_storage(blob):
    for b in blob:
        b.delete()

def delete_directory_from_datastore(path,dir_name,cur_dir):
    blob_list = blobList(cur_dir+dir_name)
    count = -1
    for i in blob_list:
        print(i.name)
        count = count + 1
        if count > 0:
            return False
    if count<=0:
        cur_user = retrieveUserInfo(session['email'])
        directory_list = cur_user['directory_list']
        i = 0 
        for d in directory_list:
            directory_key = datastore_client.key('DirectoryInfo', int(d))
            dir_ = datastore_client.get(directory_key)
            if dir_['directory_name'] == dir_name and dir_['directory_path'] == path:
                datastore_client.delete(directory_key)
                directory_list.pop(i)
                break
            i = i + 1
        cur_user.update({
            'directory_list':directory_list
        })
        datastore_client.put(cur_user)
        return True

