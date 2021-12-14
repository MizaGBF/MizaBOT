import os
import shutil

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
    dst: Destination File path
    """
    def cpy(self, src, dst):
        try: shutil.copyfile(src, dst)
        except: pass

    """mv()
    Move a file on the disk
    
    Parameters
    ----------
    src: Source File path
    dst: Destination File path
    """
    def mv(self, src, dst):
        try:
            if self.exist(src):
                if self.exist(dst): self.rm(dst) # to be sure
                shutil.move(src, dst)
        except: pass

    """exist()
    Check whatever the file exists
    
    Parameters
    ----------
    path: Path to the target
    """
    def exist(self, path):
        try: return os.path.isfile(path)
        except: return False