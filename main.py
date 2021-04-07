import datetime
from flask import Flask, render_template,session
from google.cloud import datastore,storage
import google.oauth2.id_token
from flask import Flask, render_template, request,redirect
from google.auth.transport import requests
from datetime import timedelta
from datetime import datetime
import local_constants , functions
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

@app.route('/add_directory', methods=['POST'])
def addDirectoryHandler():
    email = session['email']
    cur_user = functions.retrieveUserInfo(email)
    path = request.form['cur_dir']
    directory_name = request.form['dir_name']
    root_dir = cur_user['root_directory']
    if directory_name == '':
        return redirect('/')        #send alert to user
    if directory_name[len(directory_name) - 1] != '/':
        directory_name = directory_name + "/"
    
    if functions.check_existance_of_directory(path,directory_name,cur_user) == False:
        functions.create_directory_in_cloud_storage(root_dir,path,directory_name)
        functions.create_directory_in_datastore(directory_name,path)
        return redirect('/')
    else:
        return "Directory already exists"

@app.route('/go_to_previous_directory',methods=['POST'])
def go_to_previous_directory():
    cur_dir = request.form['cur_dir']
    splitted_dir = cur_dir.split('/')
    cur_dir = ""
    for i in range(len(splitted_dir)-2):
        cur_dir = cur_dir + splitted_dir[i]+"/"
    print(cur_dir)
    cur_user = functions.retrieveUserInfo(session['email'])
    data = functions.get_files_and_directories_at_current_path(cur_user['root_directory']+cur_dir)
    dir_list = data[0]
    file_list = data[1]
    dir_list = functions.get_directories_from_datastore_(cur_dir)
    return render_template('index.html', error_message="some error occured",cur_dir = cur_dir,dir_list = dir_list,file_list =file_list)
        

@app.route('/change_dir',methods=['POST'])
def change_dir():
    cur_dir = request.form['cur_dir']
    directory_name = request.form['directory_name']
    cur_user = functions.retrieveUserInfo(session['email'])
    # print("Path passed as parameter: "+cur_user['root_directory']+cur_dir+directory_name)
    data = functions.get_files_and_directories_at_current_path(cur_user['root_directory']+cur_dir+directory_name)
    dir_list = data[0]
    file_list = data[1]
    dir_list = functions.get_directories_from_datastore_(cur_dir+directory_name)
    # for i in dir_list:
    #     print(i.name)
    return render_template('index.html', error_message="some error occured",cur_dir = cur_dir+directory_name,dir_list = dir_list,file_list =file_list)


@app.route('/delete_directory',methods = ['GET','POST'])
def delete_directory():
    cur_dir = request.form['cur_dir']
    dir_name = request.form['dir_name']
    root_dir = functions.get_root_directory(session['email'])
    blob = functions.blobList(str(root_dir)+cur_dir+dir_name)
    # storage.Client().get_bucket(local_constants.PROJECT_STORAGE_BUCKET).blob("adil/").delete()

    if functions.delete_directory_from_datastore(cur_dir,dir_name,str(root_dir)+cur_dir):
        functions.delete_directory_or_file_from_cloud_storage(blob)
        return redirect('/')
    else:
        return "Directory Contains some file/folders, Please delete them first."
    # blob_ = functions.blobList("jawad/")
    # for b in blob_:
    #     print(b.name)
    #     b.delete()
    

@app.route('/',methods = ['POST', 'GET'])
def root():
    if request.method == 'POST':
        return render_template('index.html', error_message=error_message,cur_dir="/")
    else:
        id_token = request.cookies.get("token")
        error_message = None
        dir_list = []
        file_list = []
        if id_token:
            try:
                claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
                user_info = functions.retrieveUserInfo(claims['email'])
                if user_info == None:
                    root_directory_id = functions.createUserInfo(claims)
                    functions.create_directory_in_cloud_storage("","",str(root_directory_id)+"/")
                user_info = functions.retrieveUserInfo(claims['email'])
                session['name'] = claims['name']
                session['email'] = claims['email']
                dir_list = functions.get_directories_from_datastore_("/")
                file_list = functions.get_files_from_datastore()
            except ValueError as exc:
                error_message = str(exc)
        else:
            session['name'] = None
            session['email'] = None
        return render_template('index.html', error_message=error_message,cur_dir = "/",dir_list = dir_list,file_list =file_list)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
