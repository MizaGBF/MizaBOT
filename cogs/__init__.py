from importlib import import_module
import os
import re

DEBUG_SERVER_ID = None

def loadCogFile(bot, p, f, r, relative="", package=None):
    try:
        with open(p, mode='r', encoding='utf-8') as py:
            all = r.findall(str(py.read())) # search all matches
            for group in all:
                try:
                    module_name = f[:-3] # equal to filename without .py
                    class_name = group # the cog Class name

                    module = import_module(relative + module_name, package=package) # import
                    _class = getattr(module, class_name) # make
                    bot.add_cog(_class(bot)) # instantiate and add to the bot
                    return True
                except Exception as e:
                    print("Cog Import Exception in file", p, ":", e)
                    print("Cog Import Exception in file", p, ":", bot.util.pexc(e))
                    return False
    except Exception as e2:
        print("Cog Import Failed for file", p, ":", e2)
        print("Cog Import Exception", p, ":", bot.util.pexc(e2))
    return False

def load(bot): # load all cogs in the 'cog' folder
    global DEBUG_SERVER_ID
    try: # try to set debug server id for modules needing it
        DEBUG_SERVER_ID = bot.data.config['ids']['debug_server']
    except:
        print("Warning: 'debug_server' ID not set in 'config.json'")
        DEBUG_SERVER_ID = None
    r = re.compile("^class ([a-zA-Z0-9_]*)\\(commands\\.Cog\\):", re.MULTILINE) # to search the name class
    count = 0 # number of attempt at loading cogs
    failed = 0 # number of loading failed (ignore debug and test cogs)
    for f in os.listdir('cogs/'): # list all files
        p = os.path.join('cogs/', f)
        if f not in ['__init__.py'] and f.endswith('.py') and os.path.isfile(p): # search for valid python file
            if loadCogFile(bot, p, f, r, relative=".", package='cogs'): count += 1
            else: failed += 1
    # optional dev files
    if loadCogFile(bot, "debug.py", "debug.py", r): count += 1
    if loadCogFile(bot, "test.py", "test.py", r): count += 1
    return count, failed # return attempts