import os
from shutil import copyfile

# ----------------------------------------------------------------------------------------------------------------
# File Component
# ----------------------------------------------------------------------------------------------------------------
# Let your copy or delete local files
# ----------------------------------------------------------------------------------------------------------------

class File():
    def __init__(self, bot):
        self.bot = bot

    def init(self):
        pass

    """rm()
    Delete a file from the disk
    
    Parameters
    ----------
    filename: File path
    """
    def rm(self, filename):
        try: os.remove(filename)
        except: pass

    """cpy()
    Copy a file on the disk
    
    Parameters
    ----------
    src: Source File path
    dst: Copy File path
    """
    def cpy(self, src, dst):
        try: copyfile(src, dst)
        except: pass