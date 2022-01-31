import datetime


from flask import Flask, render_template, request, redirect, session, Response
from google.cloud import datastore
from google.cloud import storage
import google.oauth2.id_token
from google.auth.transport import requests
import re

import local_constants

app = Flask(__name__)
app.secret_key = "abc"

# get access to the datastore client so we can add and store data in the datastore
datastore_client = datastore.Client()


# get access to a request adapter for firebase as we will need this to authenticate users
firebase_request_adapter = requests.Request()

def createUserInfo(claims):
    entity_key = datastore_client.key('UserInfo', claims['email'])
    entity = datastore.Entity(key= entity_key)
    entity.update({
        'email': claims['email'],
        'name': claims['name'],
        'file_list': [],
        'dir_list': [],

    })
    datastore_client.put(entity)

def createDir(dir_name, claims):#a directory needs to be associated with a user

    entity_key = datastore_client.key('Directory', dir_name)
    entity = datastore_client.get(entity_key)
    print("dir is ", entity)
    if entity is None:
        entity = datastore.Entity(key=datastore_client.key("Directory", dir_name))
        entity.update({
            'email': claims['email'],
            'file_list': [],
            'dependent_dir': [],
        })
        datastore_client.put(entity)
    else:
        print("Dir already exists")


def createFile(file_name):#files can belong to anyone, not tied to a user on creation
    entity_key = datastore_client.key('File', file_name)
    entity = datastore.Entity(key= entity_key)
    entity.update({
        'dir_list': [],
    })
    datastore_client.put(entity)

def retrieveUserInfo(claims):
    entity_key = datastore_client.key('UserInfo', claims['email'])
    entity = datastore_client.get(entity_key)

    return entity

def blobList(prefix):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)

    return storage_client.list_blobs(local_constants.PROJECT_STORAGE_BUCKET, prefix=prefix)

def addDirectory(directory_name):
    storage_client = storage.Client(project = local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)

    blob = bucket.blob(directory_name)
    blob.upload_from_string('', content_type='application/x-www-form-urlencoded;charset=UTF-8')

def delete_blob(i_slash):

    storage_client = storage.Client(project = local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)

    blob = bucket.blob(i_slash)
    blob.delete()

def delete_file(filename):

    storage_client = storage.Client(project = local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    print("this", filename)
    blob = bucket.blob(filename)
    blob.delete()


def deleteEnt(i_slash):#delete ent from datastore
    key = datastore_client.key("Directory", i_slash)
    datastore_client.delete(key)

def deleteFileEnt(filename):#delete ent from datastore
    key = datastore_client.key("File", filename)
    datastore_client.delete(key)

def addFile(file, str_filename):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)

    blob = bucket.blob(str_filename)

    blob.upload_from_file(file)


def downloadBlob(filename):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)

    blob = bucket.blob(filename)
    return blob.download_as_bytes()



@app.route('/')
def root():
    # query firebase for the request token and set other variables to none for now
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None
    user_info = None
    email = None
    directory_list = []
    file_list = []
    special_root_dir_var = None


    # if we have an ID token then verify it against firebase if it doesn't check out then
    # log the error message that is returned
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)

            if session['folder'] is not None:
                str_session = str(session['folder'])
                slash_char = str_session.find("/")
                special_root_dir_var = str_session[0:slash_char + 1]
                print("spesh", special_root_dir_var)
                print("sesh", str_session)


            if user_info == None:
                createUserInfo(claims)
                user_info = retrieveUserInfo(claims)
                email = claims['email']

                dir_name = email + "/"
                session['folder'] = dir_name
                addDirectory(dir_name)

            special_root_dir_var = (claims['email'] + "/")


            #printing the list of dirs
            blob_list = blobList(special_root_dir_var)#the only folders a user can should be the logged in users
            for i in blob_list:
                if i.name[len(i.name) - 1] == '/':
                    print(i.name)
                    directory_list.append(i)
                else:
                    file_list.append(i)


        except ValueError as exc:
            error_message = str(exc)

    # render the template with the last times we have
    return render_template('index.html', user_data=claims, error_message=error_message, user_info=user_info, directory_list=directory_list, file_list=file_list, special_root_dir_var = special_root_dir_var)

@app.route('/add_directory', methods = ['POST'])
def addDirectoryHandler():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None
    user_info = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            directory_name = request.form['dir_name']
            if directory_name == '' or directory_name[len(directory_name) - 1] != '/':
                return redirect('/')
            #check for duplicate dirs
            blob_list = blobList(session['folder'])#any directory that is in the current directory
            for i in blob_list:
                if i.name[len(i.name) - 1] == directory_name:
                    return redirect('/')
            user_info = retrieveUserInfo(claims)

            addDirectory(session['folder'] + directory_name)
            createDir(session['folder'] + directory_name, claims) # create directory entity in datastore

        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')

@app.route('/delete_directory/<path:i>', methods = ['POST'])
def delete_directory(i):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None
    user_info = None
    print(i)
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            i_slash = (i + '/') #put the slash back in so it can be found in bucket
            print("delete folder", i_slash)
            delete_blob(i_slash)
            deleteEnt(i_slash)

        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')

@app.route('/up_directory/<path:i>', methods = ['POST'])
def up_directory(i):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None
    user_info = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

            str = session['folder']

            if str.find('/'):
                indexes = [x.start() for x in re.finditer('/', str)]
                print(indexes)
                if len(indexes) > 1:
                    second_last_char_index = indexes[-2]
                else:
                    second_last_char_index = len(str)

                #i_slash = (i + '/')#put back in terminal slash
                #string_i = str(session['folder'])
                #last_char_index = string_i.rfind("/")
                truncated_str = str[:second_last_char_index]
                session['folder'] = truncated_str + ('/')
                print("session var", session['folder'])

        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')

@app.route('/change_directory/<path:i>', methods = ['POST'])
def change_directory(i):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None
    user_info = None
    print(i)
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            i_slash = (i + '/')
            session['folder'] = i_slash
            print("hey there", session['folder'])

        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')

@app.route('/upload_file', methods = ['post'])
def uploadFileHandler():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None
    user_info = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            file = request.files['file_name']
            if file.filename == '':
                return redirect('/')
                # check for duplicate files
            blob_list = blobList(session['folder'])  # any file that is in the current directory
            for i in blob_list:
                if i.name[len(i.name) -1] == file.filename:
                    return redirect('/')
            user_info = retrieveUserInfo(claims)
            str_filename = session['folder'] + file.filename
            addFile(file, str_filename)
            createFile(str_filename)

        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


@app.route('/download_file/<path:filename>', methods = ['POST'])
def downloadFile(filename):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None
    user_info = None
    file_bytes = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)

        except ValueError as exc:
            error_message = str(exc)
    return Response(downloadBlob(filename), mimetype='application/octet-stream')

@app.route('/delete_file/<path:filename>', methods = ['POST'])
def deleteFile(filename):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None
    user_info = None
    file_bytes = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            delete_file(filename)
            deleteFileEnt(filename)
        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')








if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
