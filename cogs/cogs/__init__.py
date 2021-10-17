from importlib import import_module
import os
import re

def load(bot): # load all cogs in the 'cog' folder
    r = re.compile("^class ([a-zA-Z0-9_]*)\\(commands\\.Cog\\):", re.MULTILINE) # to search the name class
    count = 0 # number of attempt at loading cogs
    for f in os.listdir('cogs/'): # list all files
        p = os.path.join('cogs/', f)
        if f not in ['__init__.py'] and f.endswith('.py') and os.path.isfile(p): # search for valid python file
            try:
                with open(p, mode='r', encoding='utf-8') as py:
                    all = r.findall(str(py.read())) # search all matches
                    for group in all:
                        try:
                            module_name = f[:-3] # equal to filename without .py
                            class_name = group # the cog Class name

                            module = import_module('.' + module_name, package='cogs') # import
                            _class = getattr(module, class_name) # make
                            bot.add_cog(_class(bot)) # instantiate and add to the bot
                        except Exception as e:
                            print("Cog Import Exception in file", p, ":", bot.util.pexc(e))
                        count += 1
            except:
                pass

    return count # return attempts