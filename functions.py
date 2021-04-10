import datetime
from flask import Flask, render_template,session
from google.cloud import datastore,storage
import google.oauth2.id_token
from flask import Flask, render_template, request,redirect,Response,send_file
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
        'file_list':[],
        'shared_files':[]
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
    file_list.append(file_id)
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

def check_existance_of_file(path,file_name,cur_user):
    file_list = cur_user['file_list']
    for d in file_list:
        file_key = datastore_client.key('fileInfo', d)
        file_data = datastore_client.get(file_key)
        if file_data['file_path'] == path and file_data['file_name'] == file_name:
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
            # print(dir_['directory_name'])
            dir_list.append(dir_)
    return dir_list
    


def get_duplicates(path):
    print(path)
    file_list = []
    second_list = []
    blob_list = blobList(path)
    duplicate_list = []
    for i in blob_list:
        if i.name[len(i.name) - 1] != '/':  # not a directory but a file
            file_list.append(i)
            second_list.append(i)
            # print(i.md5_hash)
            print(i.name)
    
    for f in file_list:
        i = 0
        for b in second_list:
            if f.md5_hash == b.md5_hash and f.name != b.name:
                duplicate_list.append(b)
                second_list.pop(i)
            i = i + 1

    return duplicate_list

def get_duplicates_within_directory(path):
    print(path)
    file_list = []
    blob_list = blobList(path)
    path_length = len(path.split('/'))
    duplicate_list = []
    second_list = []
    for i in blob_list:
        if i.name[len(i.name) - 1] != '/':  # not a directory but a file
            if len(i.name.split('/'))>path_length:
                continue
            file_list.append(i)
            second_list.append(i)
            # print(i.md5_hash)
            print(i.name)
    
    for f in file_list:
        i = 0
        for b in second_list:
            if len(b.name.split('/'))>path_length:
                continue
            if f.md5_hash == b.md5_hash and f.name != b.name:
                duplicate_list.append(b)
                second_list.pop(i)
        # break

    return duplicate_list

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

def addFile(file,path):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(path+file.filename)
    blob.upload_from_file(file)

def get_files_from_datastore_(path):
    cur_user = retrieveUserInfo(session['email'])
    file_list = cur_user['file_list']
    files_list = []
    for d in file_list:
        # print(d)
        file_key = datastore_client.key('fileInfo', int(d))
        file_ = datastore_client.get(file_key)
        if path == file_['file_path']:
            # print(file_['file_name'])
            files_list.append(file_)
    return files_list

def delete_file_from_datastore(cur_user,path,file_name):
    file_list = cur_user['file_list']
    i = 0 
    for d in file_list:
        file_key = datastore_client.key('fileInfo', int(d))
        file_ = datastore_client.get(file_key)
        if file_['file_name'] == file_name and file_['file_path'] == path:
            datastore_client.delete(file_key)
            file_list.pop(i)
            # break
        i = i + 1
    cur_user.update({
        'file_list':file_list
    })
    datastore_client.put(cur_user)

def downloadBlob(filename):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(filename)
    return blob.download_as_bytes()

def get_all_users():
    query = datastore_client.query(kind='UserInfoForAssignment3')
    results = query.fetch()
    result_without_self = []
    for r in results:
        if r['email'] == session['email']:
            continue
        result_without_self.append(r)
    return result_without_self

def store_shared_file_path(path,user_selected):
    selected_user = retrieveUserInfo(user_selected)
    print(user_selected)
    shared_list = selected_user['shared_files']
    shared_list.append(path)
    selected_user.update({
        'shared_files':shared_list
    })
    datastore_client.put(selected_user)

def get_shared_files():
    cur_user = retrieveUserInfo(session['email'])
    return cur_user['shared_files']


