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
        # 'directory_list': [],
        # 'file_list':[],
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
    # entity_key = datastore_client.key('UserInfoForAssignment3', session['email'])
    # cur_user = datastore_client.get(entity_key)
    dir_id = random.getrandbits(63)
    directory_key = datastore_client.key('DirectoryInfo', dir_id)
    entity = datastore.Entity(key = directory_key)
    entity.update({
        'directory_name': directory_name,
        'directory_path': path,
        'owner':session['email']
    })
    datastore_client.put(entity)
    # directory_list = cur_user['directory_list']
    # directory_list.append(str(dir_id)+":"+directory_name+":"+path)
    # cur_user.update({
    #     'directory_list':directory_list
    # })
    # datastore_client.put(cur_user)

def create_file_in_datastore(file_name,path,is_shared):
    # entity_key = datastore_client.key('UserInfoForAssignment3', session['email'])
    # cur_user = datastore_client.get(entity_key)
    file_id = random.getrandbits(63)
    file_key = datastore_client.key('fileInfo', file_id)
    entity = datastore.Entity(key = file_key)
    entity.update({
        'file_name': file_name,
        'file_path': path,
        # 'is_file_shared': is_shared,
        'owner':session['email']
    })
    datastore_client.put(entity)
    # file_list = cur_user['file_list']
    # file_list.append(str(file_id)+":"+file_name+":"+path)
    # cur_user.update({
    #     'file_list':file_list
    # })
    # datastore_client.put(cur_user)

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

def check_existance_of_directory(path,dir_name):
    query = datastore_client.query(kind='DirectoryInfo')
    query.add_filter('owner','=',session['email'])
    query.add_filter('directory_path','=',path)
    query.add_filter('directory_name','=',dir_name)
    dir_list = query.fetch()
    print(path)
    # dir_list = cur_user['directory_list']
    for d in dir_list:
        # split_dirs = d.split(":")
        # # directory_key = datastore_client.key('DirectoryInfo', d)
        # # dir_data = datastore_client.get(directory_key)
        # if split_dirs[2] == path and split_dirs[1] == dir_name:
        return True
    return False

def check_existance_of_file(path,file_name):
    # file_list = cur_user['file_list']
    query = datastore_client.query(kind='fileInfo')
    query.add_filter('owner','=',session['email'])
    query.add_filter('file_path','=',path)
    query.add_filter('file_name','=',file_name)
    file_list = query.fetch()
    for f in file_list:
        # split_file = d.split(":")
        # # file_key = datastore_client.key('fileInfo', d)
        # # file_data = datastore_client.get(file_key)
        # if split_file[2] == path and split_file[1] == file_name:
        return True
    return False

def get_directories_from_datastore_(path):
    # directory_list = cur_user['directory_list']
    query = datastore_client.query(kind='DirectoryInfo')
    query.add_filter('owner','=',session['email'])
    # print(session['email'])
    query.add_filter('directory_path','=',path)
    dir_list = query.fetch()
    # # dir_list = []
    # for d in directory_list:
    #     split_dirs = d.split(":")
    #     # print(split_dirs[1])
    #     if path == split_dirs[2]:
    #         dir_list.append(split_dirs[1])  # appending the name of directory
    # for i in dir_list:
    #     print(i['directory_name'])
    return dir_list

def get_duplicates(path):
    # print(path)
    file_list = []
    second_list = []
    blob_list = blobList(path)
    duplicate_list = []
    for i in blob_list:
        if i.name[len(i.name) - 1] != '/':  # not a directory but a file
            file_list.append(i)
            second_list.append(i)
            # print(i.name)

    for f in file_list:
        i = 0
        while i < len(second_list):
            if f.md5_hash == second_list[i].md5_hash and f.name != second_list[i].name:
                duplicate_list.append(second_list[i])
                # print(second_list[i].name)
                second_list.pop(i)
                i = i - 1
            i = i + 1

    return duplicate_list

def get_duplicates_within_directory(path):
    # print(path)
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
            # print(i.name)

    for f in file_list:
        i = 0
        while i < len(second_list):
            if len(second_list[i].name.split('/'))>path_length:
                continue
            if f.md5_hash == second_list[i].md5_hash and f.name != second_list[i].name:
                duplicate_list.append(second_list[i])
                # print(second_list[i].name)
                second_list.pop(i)
                i = i - 1
            i = i + 1
        # file_list.pop(0)

    return duplicate_list

def delete_directory_or_file_from_cloud_storage(blob):
    for b in blob:
        b.delete()

def delete_directory_from_datastore(path,dir_name,cur_dir):
    dir_list = get_directories_from_datastore_(path+dir_name)
    for d in dir_list:
        return False
    file_list = get_files_from_datastore_(path+dir_name)
    for f in file_list:
        return False
    directory_list = get_directories_from_datastore_(path)
    # blob_list = blobList(cur_dir+dir_name)
    # count = -1
    # for i in blob_list:
    #     print(i.name)
    #     count = count + 1
    #     if count > 0:
    #         return False
    # if count<=0:
    #     cur_user = retrieveUserInfo(session['email'])
    #     directory_list = cur_user['directory_list']
    #     i = 0
    for d in directory_list:
        # split_dirs = d.split(":")
        directory_key = datastore_client.key('DirectoryInfo', d.key.id)
        # dir_ = datastore_client.get(directory_key)
        if d['directory_name'] == dir_name and d['directory_path'] == path:
            datastore_client.delete(directory_key)
    #         directory_list.pop(i)
    #         break
    #     i = i + 1
    # cur_user.update({
    #     'directory_list':directory_list
    # })
    # datastore_client.put(cur_user)
    return True

def addFile(file,path):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(path+file.filename)
    blob.upload_from_file(file)

def get_files_from_datastore_(path):
    # file_list = cur_user['file_list']
    query = datastore_client.query(kind='fileInfo')
    query.add_filter('owner','=',session['email'])
    query.add_filter('file_path','=',path)
    files_list = query.fetch()
    # files_list = []
    # for d in file_list:
    #     split_file = d.split(":")
    #     # file_key = datastore_client.key('fileInfo', int(d))
    #     # file_ = datastore_client.get(file_key)
    #     if path == split_file[2]:
    #         files_list.append(split_file[1])
    return files_list

def delete_file_from_datastore(path,file_name):
    # file_list = cur_user['file_list']
    query = datastore_client.query(kind='fileInfo')
    query.add_filter('owner','=',session['email'])
    query.add_filter('file_path','=',path)
    query.add_filter('file_name','=',file_name)
    file_list = query.fetch()
    # i = 0
    for d in file_list:
        # split_files = d.split(":")
        file_key = datastore_client.key('fileInfo', d.key.id)
        # file_ = datastore_client.get(file_key)
        # if split_files[1] == file_name and split_files[2] == path:
        if d['file_name'] == file_name and d['file_path'] == path:
            datastore_client.delete(file_key)
    #         file_list.pop(i)
    #     i = i + 1
    # cur_user.update({
    #     'file_list':file_list
    # })
    # datastore_client.put(cur_user)

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


