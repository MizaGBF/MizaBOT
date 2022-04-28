import os
import re
import json

func_index = {}

def make_parameters(params): # parse the raw parameter list (the list of string) and convert into html
    msg = ""
    # possible parameter formats
    # var_name
    # var_name : var_type
    # var_name : var_type = default_value
    # var_name : var_type = commands.Param(...)
    for p in params:
        pname = None
        ptype = None
        pextra = None
        cmsg = ""
        sp = p.split(':')
        if len(sp) <= 1: # var_name
            pname = sp[0].replace(' ', '')
            sp = p.split('=')
            if len(sp) >= 2:
                pextra = '='.join(sp[1:])
        else: # var_name : var_type and others...
            pname = sp[0].replace(' ', '')
            sp = ':'.join(sp[1:]).split('=')
            if len(sp) == 1:
                ptype = sp[0].replace(' ', '')
            else:
                ptype = sp[0].replace(' ', '')
                pextra = '='.join(sp[1:])
        cmsg += pname
        if ptype is not None: # converting types into more readable stuff for normal people
            cmsg += " ({})".format(ptype.replace('int', 'Integer').replace('str', 'String').replace('disnake.', ''))
        if pextra is not None: # parsing commands.Param(...)
            pos = pextra.find("description")
            if pos != -1:
                a = pextra.find('"', pos)
                b = pextra.find("'", pos)
                if a != -1 and (b == -1 or (b != -1 and a < b)):
                    pos = a + 1
                    a = pextra.find('"', pos)
                else:
                    pos = b + 1
                    a = pextra.find("'", pos)
                cmsg += "&nbsp;:&nbsp;{}".format(pextra[pos:a])

            pos = pextra.find("default")
        msg += cmsg
    if msg != "":
        msg = msg[:-4]
    return msg

def count_commands(command_list): # main function to generate the html
    # for debugging
    cmd_count = 0
    other_count = 0
    prev_count = 0
    cmd_cache = set()
    sub_count = {}
    # loop over the cogs
    for cog in command_list:
        commands = command_list[cog]
        if len(commands) == 0: continue
        # loop over those commands
        for c in commands:
            cn = "" # command name
            if c['type'] == 0: cn = "/" # slash command, we add / before
            elif c['type'] == 3:
                cn = "/{} ".format(func_index.get(cog + "_" + c['parent'], c['parent'])) # sub command, we add / and parent(s) before
                sub_count[cn] = sub_count.get(cn, 0) + 1
            cn += c['name']
            if cn in cmd_cache:
                print("Warning: Command", cn, "is present twice or more")
            else:
                cmd_cache.add(cn)
            if c.get('comment', '') != '': # add description
                if len(c['comment']) >= 100:
                    print("Warning: Command", c['name'], "description is too long")
            else:
                print("Warning:", c['name'], "has no description")
            if c['type'] == 0 or c['type'] == 3: # add command type
                out = make_parameters(c['args'])
            if c['type'] == 0:
                cmd_count += 1
            else:
                other_count += 1
        prev_count = cmd_count
    print("Total:", cmd_count, " main slash commands")
    print("Checking irregularities...")
    if cmd_count > 50:
        print("- Too many Slash commands")
    for key in sub_count:
        if sub_count[key] > 10:
            print("-", key, "has", sub_count[key],"sub commands [WARNING]")
    print("Check done")

def breakdown_parameters(raw_args): # breakdown the command definitions and retrieve the parameters
    args = []
    lvl = 0
    buf = ""
    for c in raw_args:
        if c == '(': lvl += 1
        elif c == ')': lvl -= 1
        if lvl == 0 and c == ',' :
            args.append(buf)
            buf = ""
        else:
            buf += c
    if buf != "": args.append(buf)
    return args # result is a list of string, each string being the full parameter declaration

def search_interval(data, pos, max_pos, start, end): # search a string between specific positions and strings
    s = data.find(start, pos, max_pos)
    if s == -1: return None
    e = data.find(end, s+len(start), max_pos)
    if e == -1: return None
    return data[s+len(start):e]

def retrieve_command_list(cog, data, pos_list): # use the position list to retrieve the command datas
    cl = []
    i = data.find('self.color = 0x') # retrieve the cog color
    if i != -1:
        color = data[i+len('self.color = 0x'):i+len('self.color = 0x')+6]
    else:
        color = None
    # iterate over the cog file
    for i in range(len(pos_list)):
        pos = pos_list[i][0]
        if i == len(pos_list) - 1: # if it's the last command in the list
            fp = data.find('async def ', pos)
            max_pos = len(data) - 1 # search range end
        else: # if not
            fp = data.find('async def ', pos, pos_list[i+1][0]) # we search between current position and next one
            max_pos = pos_list[i+1][0] # search range end
        if fp != -1: # if found
            c = {}
            # before anything else
            tmp = search_interval(data, pos, fp, 'name=', ')') # check if the name parameter is in the command decorator
            if tmp is not None:
                c['name'] = tmp.replace('"', '').replace("'", "") # and store it
                alias = c['name'] # take note we found a renaming
            else:
                alias = None
            base_namee = ""
            # now we check the command definition
            fp += len('async def ')
            tmp = search_interval(data, pos, max_pos, ' def ', '(') # search the function name
            if tmp is None: continue # not found? (it shouldn't happen) skip to next one
            base_name = tmp
            if alias is None: # if no renaming
                c['name'] = tmp # just store it as it is
                if c['name'].startswith('_'): c['name'] = c['name'][1:]
            else: # if it's a renamed command, store the relation in the index
                func_index[cog + "_" + tmp] = alias
            # now parse the command parameters
            args = breakdown_parameters(search_interval(data, fp, max_pos, '(', '):'))
            # remove the first two (self, inter)
            args.pop(0)
            args.pop(0)
            c['args'] = args # and store
            # retrieve the doc string (the command description)
            tmp = search_interval(data, fp, max_pos, '"""', '"""')
            if tmp is not None:
                c['comment'] = tmp.replace("        ", "")
            else:
                c['comment'] = ""
            if pos_list[i][1] == 4: # setting up sub_command_group name translation
                if alias is not None:
                    func_index[cog + "_" + base_name] = pos_list[i][2] + " " + c['name']
                else:
                    func_index[cog + "_" + c['name']] = pos_list[i][2] + " " + c['name']

            c['color'] = color # color
            c['type'] = pos_list[i][1] # function type
            if pos_list[i][1] == 3:
                c['parent'] = pos_list[i][2] # the parent if it's a sub command
            if pos_list[i][1] != 4: # don't put sub_command_group
                cl.append(c) # add to list
    return cl

def find_command_pos(data): # loop over a file and note the position of all commands
    pos_list = [] # will contain the resulting list
    cur = 0 # cursor
    while True:
        poss = [data.find('@commands.slash_command', cur), data.find('@commands.user_command', cur), data.find('@commands.message_command', cur), data.find('.sub_command(', cur), data.find('.sub_command_group(', cur)] # different command types we are searching for
        idx = -1
        while True: # messy loop used to find the lowest position in the list
            idx += 1
            if idx == 5: break
            if poss[idx] == -1: continue
            # compare other in the list with current one, continue if they are better (aka lower)
            if poss[(idx+1)%5] != -1 and poss[(idx+1)%5] <= poss[idx]: continue
            if poss[(idx+2)%5] != -1 and poss[(idx+2)%5] <= poss[idx]: continue
            if poss[(idx+3)%5] != -1 and poss[(idx+3)%5] <= poss[idx]: continue
            if poss[(idx+4)%5] != -1 and poss[(idx+4)%5] <= poss[idx]: continue
            break
        if idx == 5: break # no more command found, we stop
        if idx >= 3: # we found a sub command
            x = data.find('@', poss[idx]-15) # we retrieve the name of the parent
            pos_list.append((poss[idx], idx, data[x+1:poss[idx]])) # and add it in the tuple
        else:
            pos_list.append((poss[idx], idx)) # position and command type (0 = slash, 1 = user, 2 = message, 3 = sub_command, 4 is always ignored)
        cur = poss[idx] + 10 # update the cursor
    return pos_list

def main(): # main function
    global func_index # dictionnary for translating command groups to their names (IF renamed)
    func_index = {}
    print("Counting commands...")
    r = re.compile("^class ([a-zA-Z0-9_]*)\\(commands\\.Cog\\):", re.MULTILINE) # regex to find Cog
    command_list = {}
    for f in os.listdir('../cogs/'): # list all files (note: we don't parse the bot, debuf and test files)
        p = os.path.join('../cogs/', f) # path of the current file
        if f not in ['__init__.py'] and f.endswith('.py') and os.path.isfile(p): # search for valid python file (ignore init and other files)
            try:
                with open(p, mode='r', encoding='utf-8') as py: # open it
                    data = str(py.read())
                    all = r.findall(data) # apply the regex
                    for group in all: # for all valid results
                        try:
                            class_name = group # the cog Class name
                            cl = retrieve_command_list(class_name, data, find_command_pos(data)) # parse the content
                            if len(cl) > 0: # if at least one public command found
                                command_list[class_name] = cl # store it
                        except Exception as e:
                            print(e)
            except:
                pass
    count_commands(command_list) # generate the html using the stored data on found commands
    print("Done")

if __name__ == "__main__": # entry point
    main()