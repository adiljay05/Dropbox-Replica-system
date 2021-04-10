import datetime
from flask import Flask, render_template,session
from google.cloud import datastore,storage
import google.oauth2.id_token
from flask import Flask, render_template, request,redirect,Response,send_from_directory
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
        dir_list = functions.get_directories_from_datastore_(path)
        file_list = functions.get_files_from_datastore_(path)
        return render_template('index.html', error_message="some error occured",cur_dir = path,dir_list = dir_list,file_list =file_list)
        # return redirect('/')
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
    if cur_dir == "/":
        return redirect('/')
    cur_user = functions.retrieveUserInfo(session['email'])
    # data = functions.get_files_and_directories_at_current_path(cur_user['root_directory']+cur_dir)
    # dir_list = data[0]
    # file_list = data[1]
    dir_list = functions.get_directories_from_datastore_(cur_dir)
    file_list = functions.get_files_from_datastore_(cur_dir)
    return render_template('index.html', error_message="some error occured",cur_dir = cur_dir,dir_list = dir_list,file_list =file_list)
        

@app.route('/change_dir',methods=['POST'])
def change_dir():
    cur_dir = request.form['cur_dir']
    directory_name = request.form['directory_name']
    cur_user = functions.retrieveUserInfo(session['email'])
    # print("Path passed as parameter: "+cur_user['root_directory']+cur_dir+directory_name)
    # data = functions.get_files_and_directories_at_current_path(cur_user['root_directory']+cur_dir+directory_name)
    # dir_list = data[0]
    # file_list = data[1]
    dir_list = functions.get_directories_from_datastore_(cur_dir+directory_name)
    file_list = functions.get_files_from_datastore_(cur_dir+directory_name)
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
        dir_list = functions.get_directories_from_datastore_(cur_dir)
        file_list = functions.get_files_from_datastore_(cur_dir)
        return render_template('index.html', error_message="some error occured",cur_dir = cur_dir,dir_list = dir_list,file_list =file_list)
        # return redirect('/')
    else:
        return "Directory Contains some file/folders, Please delete them first."
    # blob_ = functions.blobList("jawad/")
    # for b in blob_:
    #     print(b.name)
    #     b.delete()
    

@app.route('/upload_file', methods=['post'])
def uploadFileHandler():
    file = request.files['file_name']
    if file.filename == '':
        return "alert('Please select a file First')"
    cur_dir = request.form['cur_dir']
    root_dir = functions.retrieveUserInfo(session['email'])['root_directory']
    path = root_dir+cur_dir
    functions.addFile(file,path)
    functions.create_file_in_datastore(file.filename,cur_dir,"no")
    return redirect('/')

@app.route('/delete_file',methods=['POST'])
def delete_file():
    file_name = request.form['file_name']
    cur_dir = request.form['cur_dir']
    cur_user = functions.retrieveUserInfo(session['email'])
    root_dir = cur_user['root_directory']
    blob = storage.Client().get_bucket(local_constants.PROJECT_STORAGE_BUCKET).blob(root_dir+cur_dir+file_name)
    functions.delete_file_from_datastore(cur_user,cur_dir,file_name)
    # print(blob.name)
    blob.delete()
    dir_list = functions.get_directories_from_datastore_(cur_dir)
    file_list = functions.get_files_from_datastore_(cur_dir)
    return render_template('index.html', error_message="some error occured",cur_dir = cur_dir,dir_list = dir_list,file_list =file_list)
    # return redirect('/')

@app.route('/check_duplicates_entire_storage',methods=['POST'])
def check_duplicates_entire_storage():
    cur_user = functions.retrieveUserInfo(session['email'])
    duplicates = functions.get_duplicates(cur_user['root_directory']+"/")
    return render_template('duplicates.html',msg="Duplicates in Entire User Storage",duplicates = duplicates)

@app.route('/check_duplicates_in_current_directory',methods = ['POST'])
def check_duplicates_in_current_directory():
    cur_dir = request.form['cur_dir']
    cur_user = functions.retrieveUserInfo(session['email'])
    duplicates = functions.get_duplicates_within_directory(cur_user['root_directory']+cur_dir)
    return render_template('duplicates.html',msg="Duplicates in "+cur_dir,duplicates = duplicates)

@app.route('/download_file',methods=['POST'])
def download_file():
    cur_user = functions.retrieveUserInfo(session['email'])
    file_name = request.form['file_name']
    cur_dir = request.form['cur_dir']
    # return send_from_directory(cur_user['root_directory']+cur_dir+file_name,file_name,as_attachment=True)
    return Response(functions.downloadBlob(cur_user['root_directory']+cur_dir+file_name), mimetype='application/octet-stream', headers={"Content-Disposition": "filename="+file_name})

@app.route('/download_shared_file',methods=['POST'])
def download_shared_file():
    path_with_name = request.form['path_with_name']
    splitted_path = path_with_name.split('/')
    file_name = splitted_path.pop()
    return Response(functions.downloadBlob(path_with_name), mimetype='application/octet-stream', headers={"Content-Disposition": "filename="+file_name})

@app.route('/share_file',methods=['POST'])
def share_file():
    file_name = request.form['file_name']
    cur_dir = request.form['cur_dir']
    users = functions.get_all_users()
    cur_user = functions.retrieveUserInfo(session['email'])
    return render_template('share_file.html',cur_dir = cur_user['root_directory']+cur_dir, file_name = file_name,users = users)

@app.route('/share_file_now',methods=['POST'])
def share_file_now():
    file_name = request.form['file_name']
    cur_dir = request.form['cur_dir']
    user_selected = request.form['user_selected']
    functions.store_shared_file_path(cur_dir+file_name,user_selected)
    return "shared"
    

@app.route('/',methods = ['POST', 'GET'])
def root():
    if request.method == 'POST':
        return render_template('index.html', error_message=error_message,cur_dir="/")
    else:
        id_token = request.cookies.get("token")
        error_message = None
        dir_list = []
        file_list = []
        shared_files = []
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
                file_list = functions.get_files_from_datastore_("/")
                shared_files = functions.get_shared_files()
            except ValueError as exc:
                error_message = str(exc)
        else:
            session['name'] = None
            session['email'] = None
        return render_template('index.html', error_message=error_message,cur_dir = "/",dir_list = dir_list,file_list =file_list,shared_files = shared_files)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
