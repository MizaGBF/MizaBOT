from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import threading
import json
from datetime import datetime
import multiprocessing
from ctypes import c_int

# ----------------------------------------------------------------------------------------------------------------
# Drive Component
# ----------------------------------------------------------------------------------------------------------------
# This component manages the save data file (save.json) over Google Drive
# It also lets you send and retrieve files from Google Drive for whatever application you might need
#
# IMPORTANT
# all interactions with Google Drive is made in another process to mitigate a possible memory leak
# this will be reverted back if a fix is found
# ----------------------------------------------------------------------------------------------------------------

def access():
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("credentials.json") # load credentials
    if gauth.credentials is None: # if failed, get them
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired: # or if expired, refresh
        gauth.Refresh()
    else:
        gauth.Authorize() # good
    gauth.SaveCredentialsFile("credentials.json") # save
    return GoogleDrive(gauth)

def load(folder, ret): # load save.json from the folder id in bot.tokens
    try:
        drive = access()
        file_list = drive.ListFile({'q': "'" + folder + "' in parents and trashed=false"}).GetList() # get the file list in our folder
        # search the save file
        for s in file_list:
            if s['title'] == "save.json":
                s.GetContentFile(s['title']) # iterate until we find save.json and download it
                ret.value = 1
                return
        ret.value = -1
    except Exception as e:
        print(e)
        ret.value = 0

def save(data, folder, ret): # write save.json to the folder id in bot.tokens
    try:
        drive = access()
        prev = []
        # backup
        file_list = drive.ListFile({'q': "'" + folder + "' in parents and trashed=false"}).GetList()
        if len(file_list) > 9: # delete if we have too many backups
            for f in file_list:
                if f['title'].find('backup') == 0:
                    f.Delete()
        for f in file_list: # search the previous save(s)
            if f['title'] == "save.json":
                prev.append(f)
        # saving
        s = drive.CreateFile({'title':'save.json', 'mimeType':'text/JSON', "parents": [{"kind": "drive#file", "id": folder}]})
        s.SetContentString(data)
        s.Upload()
        # rename the previous save(s)
        for f in prev:
            f['title'] = "backup_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".json"
            f.Upload()
        ret.value = 1
    except Exception as e:
        print(e)
        ret.value = 0

def saveFile(data, name, folder, ret): # write a json file to a folder
    try:
        drive = access()
        s = drive.CreateFile({'title':name, 'mimeType':'text/JSON', "parents": [{"kind": "drive#file", "id": folder}]})
        s.SetContentString(data)
        s.Upload()
        ret.value = 1
    except:
        ret.value = 0

def saveDiskFile(target, mime, name, folder, ret): # write a file from the local storage to a drive folder
    try:
        drive = access()
        s = drive.CreateFile({'title':name, 'mimeType':mime, "parents": [{"kind": "drive#file", "id": folder}]})
        s.SetContentFile(target)
        s.Upload()
        ret.value = 1
    except:
        ret.value = 0

def overwriteFile(target, mime, name, folder, ret): # write a file from the local storage to a drive folder (replacing an existing one, if it exists)
    try:
        drive = access()
        file_list = drive.ListFile({'q': "'" + folder + "' in parents and trashed=false"}).GetList() # get the file list in our folder
        for s in file_list:
            if s['title'] == name:
                new_file = drive.CreateFile({'id': s['id']})
                new_file.SetContentFile(target)
                new_file.Upload()
                ret.value = 1
                return
        # not found
        saveDiskFile(target, mime, name, folder, ret)
    except Exception as e:
        print(e)
        ret.value = 0

def mvFile(name, folder, new, ret): # rename a file from a folder
    try:
        drive = access()
        file_list = drive.ListFile({'q': "'" + folder + "' in parents and trashed=false"}).GetList() # get the file list in our folder
        for s in file_list:
            if s['title'] == name:
                s['title'] = new # iterate until we find the file and change name
                s.Upload()
                ret.value = 1
                return
        ret.value = 0
    except Exception as e:
        print(e)
        ret.value = 0

def cpyFile(name, folder, new, ret): # rename a file from a folder
    try:
        drive = access()
        file_list = drive.ListFile({'q': "'" + folder + "' in parents and trashed=false"}).GetList() # get the file list in our folder
        for s in file_list:
            if s['title'] == name:
                drive.auth.service.files().copy(fileId=s['id'], body={"parents": [{"kind": "drive#fileLink", "id": folder}], 'title': new}).execute()
                ret.value = 1
        ret.value = 0
    except Exception as e:
        print(e)
        ret.value = 0

def dlFile(name, folder, ret): # load a file from a folder to the local storage
    try:
        drive = access()
        file_list = drive.ListFile({'q': "'" + folder + "' in parents and trashed=false"}).GetList() # get the file list in our folder
        for s in file_list:
            if s['title'] == name:
                s.GetContentFile(s['title']) # iterate until we find the file and download it
                ret.value = 1
                return
        ret.value = 0
    except Exception as e:
        print(e)
        ret.value = 0

def delFiles(names, folder, ret): # delete matching files from a folder
    try:
        drive = access()
        file_list = drive.ListFile({'q': "'" + folder + "' in parents and trashed=false"}).GetList() # get the file list in our folder
        for s in file_list:
            if s['title'] in names:
                s.Delete()
        ret.value = 1
    except Exception as e:
        print(e)
        ret.value = 0

# component
class Drive():
    def __init__(self, bot):
        self.bot = bot
        self.lock = threading.Lock()

    def init(self):
        pass

    def do(self, func, *args):
        ret = multiprocessing.Value(c_int, 0)
        p = multiprocessing.Process(target=func, args=args + (ret,))
        p.start()
        p.join()
        if ret.value == 0: return False
        elif ret.value > 0: return True
        return None

    def load(self): # load save.json from the folder id in bot.tokens
        with self.lock:
            r = self.do(load, self.bot.data.config['tokens']['drive'])
            if r is None:
                with open('save.json', 'w') as outfile:
                    data = self.bot.data.checkData({})
                    json.dump(data, outfile, default=self.bot.util.json_serial)
                    self.bot.data.pending = True
                return True
            return r

    def save(self, data): # write save.json to the folder id in bot.tokens
        with self.lock:
            return self.do(save, data, self.bot.data.config['tokens']['drive'])

    def saveFile(self, data, name, folder): # write a json file to a folder
        with self.lock:
            return self.do(saveFile, data, name, folder)

    def saveDiskFile(self, target, mime, name, folder): # write a file from the local storage to a drive folder
        with self.lock:
            return self.do(saveDiskFile, target, mime, name, folder)

    def overwriteFile(self, target, mime, name, folder): # write a file from the local storage to a drive folder (replacing an existing one, if it exists)
        with self.lock:
            return self.do(overwriteFile, target, mime, name, folder)

    def mvFile(self, name, folder, new): # rename a file from a folder
        with self.lock:
            return self.do(mvFile, name, folder, new)

    def cpyFile(self, name, folder, new): # rename a file from a folder
        with self.lock:
            return self.do(cpyFile, name, folder, new)

    def dlFile(self, name, folder): # load a file from a folder to the local storage
        with self.lock:
            return self.do(dlFile, name, folder)

    def delFiles(self, names, folder): # delete matching files from a folder
        return self.do(delFiles, names, folder)