from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import threading
import json
from datetime import datetime
import multiprocessing
from ctypes import c_int
import io
import gzip
import lzma
import os

# ----------------------------------------------------------------------------------------------------------------
# Drive Component
# ----------------------------------------------------------------------------------------------------------------
# This component manages the save data file (save.json) over Google Drive
# It also lets you send and retrieve files from Google Drive for whatever application you might need
#
# IMPORTANT
# all interactions with Google Drive is made in another process, using the multiprocessing module, to mitigate a possible memory leak
# this will be reverted back if a fix is found
# ----------------------------------------------------------------------------------------------------------------

"""decompressJSON_old()
Decompress the given byte array (which must be valid compressed gzip data) and return the decoded text (utf-8).

Returns
--------
str: Decompressed string
"""
def decompressJSON_old(inputBytes):
    with io.BytesIO() as bio:
        with io.BytesIO(inputBytes) as stream:
            decompressor = gzip.GzipFile(fileobj=stream, mode='r')
            while True:  # until EOF
                chunk = decompressor.read(8192)
                if not chunk:
                    decompressor.close()
                    bio.seek(0)
                    return bio.read().decode("utf-8")
                bio.write(chunk)
            return None

"""decompressJSON()
Decompress the given byte array (which must be valid compressed lzma data) and return the decoded text (utf-8).

Returns
--------
str: Decompressed string
"""
def decompressJSON(inputBytes):
    with io.BytesIO() as bio:
        with io.BytesIO(inputBytes) as stream:
            decompressor = lzma.LZMADecompressor()
            while not decompressor.eof:  # until EOF
                chunk = decompressor.decompress(stream.read(8192), max_length=8192)
                if decompressor.eof:
                    if len(chunk) > 0: bio.write(chunk)
                    bio.seek(0)
                    return bio.read().decode("utf-8")
                bio.write(chunk)
            return None

"""compressJSON()
Read the given string, encode it in utf-8, compress the data and return it as a byte array.
json.dumps() must have been used before this function.

Returns
--------
bytes: Compressed string
"""
def compressJSON(inputString):
    with io.BytesIO() as bio:
        bio.write(inputString.encode("utf-8"))
        bio.seek(0)
        buffers = []
        with io.BytesIO() as stream:
            compressor = lzma.LZMACompressor()
            while True:  # until EOF
                chunk = bio.read(8192)
                if not chunk: # EOF?
                    buffers.append(compressor.flush())
                    return b"".join(buffers)
                buffers.append(compressor.compress(chunk))

"""access()
Return a valid GoogleDrive instance

Returns
--------
GoogleDrive: Drive instance
"""
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

"""load()
Download save.json from a specified folder

Parameters
----------
folder: Google Drive Folder ID
ret: Store the return value
"""
def load(folder, ret): # load save.json from the folder id in bot.tokens
    try:
        drive = access()
        file_list = drive.ListFile({'q': "'" + folder + "' in parents and trashed=false"}).GetList() # get the file list in our folder
        # search the save file
        for s in file_list:
            if s['title'] == "save.gzip":
                s.GetContentFile(s['title']) # iterate until we find save.gzip and download it
                with open("save.gzip", "rb") as stream:
                    with open("save.json", "w") as out:
                        out.write(decompressJSON_old(stream.read()))
                os.remove("save.gzip")
                ret.value = 1
                return
            elif s['title'] == "save.lzma":
                s.GetContentFile(s['title']) # iterate until we find save.lzma and download it
                with open("save.lzma", "rb") as stream:
                    with open("save.json", "w") as out:
                        out.write(decompressJSON(stream.read()))
                os.remove("save.lzma")
                ret.value = 1
                return
        # legacy
        for s in file_list:
            if s['title'] == "save.json":
                s.GetContentFile(s['title']) # iterate until we find save.json and download it
                ret.value = 1
                return
        ret.value = -1
    except Exception as e:
        print(e)
        ret.value = 0

"""save()
Upload save.json to a specified folder

Parameters
----------
data: Save data
folder: Google Drive Folder ID
ret: Store the return value
"""
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
            if f['title'] == "save.json" or f['title'] == "save.gzip" or f['title'] == "save.lzma":
                prev.append(f)
        # compress
        cdata = compressJSON(data)
        # saving
        s = drive.CreateFile({'title':'save.lzma', 'mimeType':'	application/x-lzma', "parents": [{"kind": "drive#file", "id": folder}]})
        with io.BytesIO(cdata) as stream:
            s.content = stream
            s.Upload()
        # rename the previous save(s)
        for f in prev:
            f['title'] = "backup_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "." + f['title'].split(".")[-1]
            f.Upload()
        ret.value = 1
    except Exception as e:
        print(e)
        ret.value = 0

"""save()
Upload a json file to a specified folder

Parameters
----------
data: File data
name: File name
folder: Google Drive Folder ID
ret: Store the return value
"""
def saveFile(data, name, folder, ret): # write a json file to a folder
    try:
        drive = access()
        s = drive.CreateFile({'title':name, 'mimeType':'text/JSON', "parents": [{"kind": "drive#file", "id": folder}]})
        with io.BytesIO() as stream:
            stream.write(data.encode('utf-8'))
            s.content = stream
            s.Upload()
        ret.value = 1
    except:
        ret.value = 0

"""saveDiskFile()
Upload a file to a specified folder

Parameters
----------
target: File to save
mile: File mime type
name: File name
folder: Google Drive Folder ID
ret: Store the return value
"""
def saveDiskFile(target, mime, name, folder, ret): # write a file from the local storage to a drive folder
    try:
        drive = access()
        s = drive.CreateFile({'title':name, 'mimeType':mime, "parents": [{"kind": "drive#file", "id": folder}]})
        with open(target, "rb") as stream:
            s.content = stream
            s.Upload()
        ret.value = 1
    except:
        ret.value = 0

"""overwriteFile()
Upload a file to a specified folder, overwrite an existing file if it exists

Parameters
----------
target: File to save
mile: File mime type
name: File name
folder: Google Drive Folder ID
ret: Store the return value
"""
def overwriteFile(target, mime, name, folder, ret): # write a file from the local storage to a drive folder (replacing an existing one, if it exists)
    try:
        drive = access()
        file_list = drive.ListFile({'q': "'" + folder + "' in parents and trashed=false"}).GetList() # get the file list in our folder
        for s in file_list:
            if s['title'] == name:
                new_file = drive.CreateFile({'id': s['id']})
                with open(target, "rb") as stream:
                    s.content = stream
                    s.Upload()
                ret.value = 1
                return
        # not found
        saveDiskFile(target, mime, name, folder, ret)
    except Exception as e:
        print(e)
        ret.value = 0

"""mvFile()
Rename a file in a folder

Parameters
----------
name: File name
folder: Google Drive Folder ID
name: New File name
ret: Store the return value
"""
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

"""cpyFile()
Duplicate a file in a folder

Parameters
----------
name: File name
folder: Google Drive Folder ID
name: New File name
ret: Store the return value
"""
def cpyFile(name, folder, new, ret): # rename a file from a folder
    try:
        drive = access()
        file_list = drive.ListFile({'q': "'" + folder + "' in parents and trashed=false"}).GetList() # get the file list in our folder
        for s in file_list:
            if s['title'] == name:
                drive.auth.service.files().copy(fileId=s['id'], body={"parents": [{"kind": "drive#fileLink", "id": folder}], 'title': new}).execute()
                ret.value = 1
                return
        ret.value = 0
    except Exception as e:
        print(e)
        ret.value = 0

"""dlFile()
Download a file from a folder

Parameters
----------
name: File name
folder: Google Drive Folder ID
ret: Store the return value
"""
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

"""delFiles()
Delete files from a folder

Parameters
----------
names: List of File names
folder: Google Drive Folder ID
ret: Store the return value
"""
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

    """do()
    Run a function in a separate process
    
    Parameters
    ----------
    func: Function to be called
    *args: Parameters
    
    Returns
    --------
    bool: Return value of the function (None if invalid)
    """
    def do(self, func, *args):
        ret = multiprocessing.Value(c_int, 0)
        p = multiprocessing.Process(target=func, args=args + (ret,))
        p.start()
        p.join()
        p.close()
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