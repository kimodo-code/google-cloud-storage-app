# google-cloud-storage-app
Stores images and files in the cloud

def createUserInfo(claims): 
This function creates a UserInfo entity in the datastore with the logged in user’s email as the entity key. Other properties include a list of file and directories associated with the user. Users are already associated with directories and files in the cloud bucket but they are included as properties here in case this information is needed at a later stage. 
def createDir(dir_name, claims): 
This function creates a directory entity in the datastore with the directory name as the key and the user’s email as a property. The if statement prevents directories from being overwritten. 
def createFile(file_name): 
In a similar fashion, a file entity was created. This time there is no user property. This is to allow sharing of files at a later stage. 
def retrieveUserInfo(claims): 
This function returns the UserInfo object. 
def blobList(prefix): 
This function allows the programme to list the items in the bucket. The item list can be filtered by using the prefix. 
def addDirectory(directory_name): 
This function uses information factored out into the file - local_constants.py - to add a directory to the cloud bucket, using the accepted Google Cloud parameters. 
def delete_blob(i_slash): 
This is the function that deletes directories from the bucket. Argument is passed in from the delete_directory handler function. 
def delete_file(filename): 
This function deletes files from the bucket. Argument is passed in from the deleteFile handler function.
def deleteEnt(i_slash): 
This deletes directory entities from the datastore. This function is always called in tandem with the function that deletes directories from the bucket. 
def deleteFileEnt(filename): 
This function deletes files from the datastore 
def addFile(file): 
This function is called in the upload file handler. It adds the file to the bucket. 
def downloadBlob(filename): 
This is used to download files using the special download_as_bytes function. 
@app.route('/') 
def root(): 
There are some quite varied things that are going on here in the root function. First off, so as to create a root directory for a user as soon as they log in, when the user info is being created for the first time (when UserInfo is None), the email of the user is paired with a trailing slash and then is passed as an argument to both the datastore and the cloud bucket add directory functions. A session variable is set to the users root directory. This creates a root directory of “user_email/”. All subsequent folders are added as children of this root directory. The bloblist function has a prefix of this root folder, it is impossible to navigate above this directory using the controls, therefore all folders that this user creates are accessible only to this user. 
The if session variable is not None statement is to do with blocking the Current Working Directory display when the user is in their root directory. The session variable stores what directory the user is “in”. So that the application knows what the root directory is, a variable called special_root_dir_var is set to equal the session variable when the root directory is first created, and then is left untouched while the session variable navigates through folders. These two variables are passed to the current working directory text box in the index.html file where a javascript function compares them. If the two strings are equal (the current session variable folder is the same as the root folder) then the javascript updates the CWD textbox with a null value. If they’re not equal, then the CWD textbox is updated with the current folder - as stored in the session variable. 
Finally, to print the list of directories, a for loop goes through all the blob objects in the bucket, be they files or directories, if they have a trailing slash they’re added to the directory list, if not, they’re added to the file list, and both these lists are passed to the index.html file for display. 
@app.route('/add_directory', methods = ['POST'])
def addDirectoryHandler(): 
The add directory handler adds directories to the bucket and directory entities to the datastore. There are two if clauses for safety here, the first returns a redirect if the user doesn’t enter a directory name, the second requires that the entered directory name not match any of the directories already in the current directory - blob_list = blobList(session['folder']), iterate through looking for matches. If that checks out ok, then the directory string is concatenated with the session variable string so as to add the directory to the correct location, then it is added to the bucket. There is a further block on matching directory names located inside the add directory entity to the datastore function, to ensure consistency between the bucket and the datastore. 
@app.route('/delete_directory/<path:i>', methods = ['POST']) 
def delete_directory(i): 
The delete directory function gets the name of the directory through the url after the delete button is clicked and the information is sent from the html file. Then both the delete directory in bucket and delete directory from datastore functions are called. 
@app.route('/up_directory/<path:i>', methods = ['POST']) 
def up_directory(i): 
This function moves up the directory structure by altering the session variable which is then displayed in the CWD box, alerting the user to which directory they’re currently in. This is done by slicing off the parts of the path string that come after the second last slash, every time a “move up” button is clicked. Therefore root/test/hello/ becomes root/test/ after one click, then after a second click, the session variable is set to root, however this will not display in the CWD box as the assignment brief requests that the root directory not display. 
How this is achieved in practise is that a list of index locations is created that corresponds to where the slashes are, the second last one is extracted and then a substring is created that runs from the start of the string to this second last index location. There are also some restrictions here to prevent the programme trying to access null list indexes. 
@app.route('/change_directory/<path:i>', methods = ['POST']) 
def change_directory(i): 
This function has its start in the index.html file where a for loop creates a “Select” button beside every directory. When that button is clicked, the information is passed in through the URL to here and the session variable is updated to match the directory of the button click. As the info persists in the session variable, the change is reflected in the current working directory text box which uses the session variable to display the current directory. 
@app.route('/upload_file', methods = ['post']) 
def uploadFileHandler():
This takes in the filename from the form field, if the filename is empty then the page redirects. If not, then the add file functions for both the bucket and datastore are called and the file and filename is passed as an argument. The filename is adjusted from when the user enters it to include the current working directory, as stored in the session variable, so that the file is not added outside any folder but inside the users directory tree. 
@app.route('/download_file/<path:filename>', methods = ['POST']) 
def downloadFile(filename): 
When the download button is clicked next to a file, the file name is passed in through the URL. This function returns a Response calling the downloadBlob method and specifying the mimetype = application/octet-stream. This is so that the browser knows that the file is to be downloaded, and should not attempt to display it on the web page. 
@app.route('/delete_file/<path:filename>', methods = ['POST']) 
def deleteFile(filename): 
Similar to the other functions - the delete button next to the file, when clicked, passes the name of the file in through the URL. Both the datastore and bucket delete functions are then called. 

