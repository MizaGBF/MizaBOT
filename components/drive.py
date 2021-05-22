from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import threading
import json
from datetime import datetime

# ----------------------------------------------------------------------------------------------------------------
# Drive Component
# ----------------------------------------------------------------------------------------------------------------
# This component manages the save data file (save.json) over Google Drive
# It also lets you send and retrieve files from Google Drive for whatever application you might need
# ----------------------------------------------------------------------------------------------------------------

class Drive():
    def __init__(self, bot):
        self.bot = bot
        self.gauth = None
        self.lock = threading.Lock()

    def init(self):
        pass

    def access(self): # check credential, update if needed. Run this function on your own once to get the json, before pushing it to heroku
        try:
            if self.gauth is None:
                self.gauth = GoogleAuth()
                self.gauth.LoadCredentialsFile("credentials.json") # load credentials
                if self.gauth.credentials is None: # if failed, get them
                    self.gauth.LocalWebserverAuth()
                elif self.gauth.access_token_expired: # or if expired, refresh
                    self.gauth.Refresh()
                else:
                    self.gauth.Authorize() # good
                self.gauth.SaveCredentialsFile("credentials.json") # save
            else:
                if self.gauth.access_token_expired: # if expired, refresh
                    self.gauth.Refresh()
                    self.gauth.SaveCredentialsFile("credentials.json") # save
            return GoogleDrive(self.gauth)
        except Exception as e:
            print('Exception: ' + str(e))
            return None

    def load(self): # load save.json from the folder id in bot.tokens
        with self.lock:
            try:
                drive = self.access()
                file_list = drive.ListFile({'q': "'" + self.bot.data.config['tokens']['drive'] + "' in parents and trashed=false"}).GetList() # get the file list in our folder
                # search the save file
                for s in file_list:
                    if s['title'] == "save.json":
                        s.GetContentFile(s['title']) # iterate until we find save.json and download it
                        return True
                #if no save file on google drive, make an empty one
                with open('save.json', 'w') as outfile:
                    data = self.bot.data.checkData({})
                    json.dump(data, outfile, default=self.bot.util.json_serial)
                    self.bot.data.pending = True
                return True
            except Exception as e:
                print(e)
                return False

    def save(self, data): # write save.json to the folder id in bot.tokens
        with self.lock:
            try:
                drive = self.access()
                prev = []
                # backup
                file_list = drive.ListFile({'q': "'" + self.bot.data.config['tokens']['drive'] + "' in parents and trashed=false"}).GetList()
                if len(file_list) > 9: # delete if we have too many backups
                    for f in file_list:
                        if f['title'].find('backup') == 0:
                            f.Delete()
                for f in file_list: # search the previous save(s)
                    if f['title'] == "save.json":
                        prev.append(f)
                # saving
                s = drive.CreateFile({'title':'save.json', 'mimeType':'text/JSON', "parents": [{"kind": "drive#file", "id": self.bot.data.config['tokens']['drive']}]})
                s.SetContentString(data)
                s.Upload()
                # rename the previous save(s)
                for f in prev:
                    f['title'] = "backup_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".json"
                    f.Upload()
                return True
            except Exception as e:
                print(e)
                return False

    def saveFile(self, data, name, folder): # write a json file to a folder
        with self.lock:
            try:
                drive = self.access()
                s = drive.CreateFile({'title':name, 'mimeType':'text/JSON', "parents": [{"kind": "drive#file", "id": folder}]})
                s.SetContentString(data)
                s.Upload()
                return True
            except:
                return False

    def saveDiskFile(self, target, mime, name, folder): # write a file from the local storage to a drive folder
        with self.lock:
            try:
                drive = self.access()
                s = drive.CreateFile({'title':name, 'mimeType':mime, "parents": [{"kind": "drive#file", "id": folder}]})
                s.SetContentFile(target)
                s.Upload()
                return True
            except:
                return False

    def overwriteFile(self, target, mime, name, folder): # write a file from the local storage to a drive folder (replacing an existing one, if it exists)
        with self.lock:
            try:
                drive = self.access()
                file_list = drive.ListFile({'q': "'" + folder + "' in parents and trashed=false"}).GetList() # get the file list in our folder
                for s in file_list:
                    if s['title'] == name:
                        new_file = drive.CreateFile({'id': s['id']})
                        new_file.SetContentFile(target)
                        new_file.Upload()
                        return True
                # not found
                return self.saveDiskFile(target, mime, name, folder)
            except Exception as e:
                print(e)
                return False

    def mvFile(self, name, folder, new): # rename a file from a folder
        with self.lock:
            try:
                drive = self.access()
                file_list = drive.ListFile({'q': "'" + folder + "' in parents and trashed=false"}).GetList() # get the file list in our folder
                for s in file_list:
                    if s['title'] == name:
                        s['title'] = new # iterate until we find the file and change name
                        s.Upload()
                        return True
                return False
            except Exception as e:
                print(e)
                return False

    def cpyFile(self, name, folder, new): # rename a file from a folder
        with self.lock:
            try:
                drive = self.access()
                file_list = drive.ListFile({'q': "'" + folder + "' in parents and trashed=false"}).GetList() # get the file list in our folder
                for s in file_list:
                    if s['title'] == name:
                        drive.auth.service.files().copy(fileId=s['id'], body={"parents": [{"kind": "drive#fileLink", "id": folder}], 'title': new}).execute()
                        return True
                return False
            except Exception as e:
                print(e)
                return False

    def dlFile(self, name, folder): # load a file from a folder to the local storage
        with self.lock:
            try:
                drive = self.access()
                file_list = drive.ListFile({'q': "'" + folder + "' in parents and trashed=false"}).GetList() # get the file list in our folder
                for s in file_list:
                    if s['title'] == name:
                        s.GetContentFile(s['title']) # iterate until we find the file and download it
                        return True
                return False
            except Exception as e:
                print(e)
                return False

    def delFiles(self, names, folder): # delete matching files from a folder
        with self.lock:
            try:
                drive = self.access()
                file_list = drive.ListFile({'q': "'" + folder + "' in parents and trashed=false"}).GetList() # get the file list in our folder
                for s in file_list:
                    if s['title'] in names:
                        s.Delete()
                return True
            except Exception as e:
                print(e)
                return False