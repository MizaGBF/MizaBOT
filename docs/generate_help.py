import os
import re

func_index = {}

def get_version(): # retrieve the bot version from bot.py
    with open("../bot.py", "r", encoding="utf-8") as f:
        data = f.read()
    return search_interval(data, 0, len(data)-1, 'self.version = "', '"')

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
            if pos != -1:
                cmsg = "<b>(Optional)</b>&nbsp;" + cmsg
        msg += cmsg + "<br>"
    if msg != "":
        msg = msg[:-4]
    return msg

def generate_html(command_list): # main function to generate the html
    # various "blocks" of the page
    ver = get_version()
    metadata = '<!--This page is automatically generated, please excuse the poor formatting--><head><title>MizaBOT Online Help v{}</title><meta name="title" content=" MizaBOT Online Help v{}"><meta name="description" content="Online Help and Command List for the Granblue Fantasy Discord bot MizaBOT."><meta property="og:type" content="website"><meta property="og:url" content="https://mizagbf.github.io/MizaBOT/"><meta property="og:title" content=" MizaBOT Online Help v{}"><meta property="og:description" content="Online Help and Command List for the Granblue Fantasy Discord bot MizaBOT."><meta property="og:image" content="https://mizagbf.github.io/MizaBOT/img/card.png"><meta property="twitter:card" content="summary_large_image"><meta property="twitter:url" content="https://mizagbf.github.io/MizaBOT/"><meta property="twitter:title" content=" MizaBOT Online Help v{}"><meta property="twitter:description" content="Online Help and Command List for the Granblue Fantasy Discord bot MizaBOT."><meta property="twitter:image" content="https://mizagbf.github.io/MizaBOT/img/card.png"><link rel="icon" type="image/png" href="img/icon.png" /></head>\n'.format(ver, ver, ver, ver)
    header = '<h1 style="width:630px;margin-left: auto; margin-right: auto;"><img src="img/icon.png" style="vertical-align:middle;border-radius: 50%;box-shadow: 0 0 0 2pt #981cd6">&nbsp;MizaBOT Online Help<br>&nbsp;<small>v{}</small></h1>\n'.format(ver)
    tabs = '''<div class="tab"><button class="tablinks" onclick="openTab(event, 'Commands')">Commands</button><button class="tablinks" onclick="openTab(event, 'Guide')">Guide</button><button class="tablinks" onclick="openTab(event, 'FAQ')">FAQ</button></div>'''
    filters = '<div id="buttons"><button class="btn active" onclick="filterSelection(\'all\')" style="background: #050505;">All</button>\n'
    containers = '<ul id="commandList">\n'
    # used for command type blocks
    cmd_color_type = ['92b3e8', '92e8a3', 'e892c8', 'ffcf8c']
    cmd_type = ['Slash Command', 'User Command', 'Message Command', 'Sub Command']
    # for debugging
    cmd_count = 0
    other_count = 0
    prev_count = 0
    cmd_cache = set()
    # loop over the cogs
    for cog in command_list:
        commands = command_list[cog]
        if len(commands) == 0: continue
        # add a block
        filters += '<button class="btn" onclick="filterSelection(\'{}\')" style="background: #{};">{}</button>\n'.format(cog.lower(), commands[0].get('color', '615d5d'), cog)
        # loop over those commands
        for c in commands:
            cn = "" # command name
            if c['type'] == 0: cn = "/" # slash command, we add / before
            elif c['type'] == 3: cn = "/{} ".format(func_index.get(cog + "_" + c['parent'], c['parent'])) # sub command, we add / and parent(s) before
            cn += c['name']
            if cn in cmd_cache:
                print("Warning: Command", cn, "is present twice or more")
            else:
                cmd_cache.add(cn)
        
            # command container
            containers += '<li class="command {}"><div class="command-name"><span style="display: inline-block;background: #{};padding: 5px;text-shadow: 2px 2px 2px rgba(0,0,0,0.5);">{}</span>&nbsp;<span style="display: inline-block;background: #{};padding: 3px;text-shadow: 2px 2px 2px rgba(0,0,0,0.5); font-size: 14px;">{}</span>&nbsp;&nbsp;{}'.format(cog.lower(), c.get('color', '615d5d'), cog, cmd_color_type[c['type']], cmd_type[c['type']], cn)
            if c.get('comment', '') != '': # add description
                containers += '</div><div class="command-description"><b>Description :</b>&nbsp;{}'.format(c['comment'].replace('(Mod Only)', '<b>(Mod Only)</b>').replace('((You) Mod Only)', '<b>((You) Mod Only)</b>').replace('(NSFW channels Only)', '<b>(NSFW channels Only)</b>'))
                if len(c['comment']) >= 100:
                    print("Warning: Command", c['name'], "description is too long")
            else:
                print("Warning:", c['name'], "has no description")
            if c['type'] == 0 or c['type'] == 3: # add command type
                out = make_parameters(c['args'])
                if out != '':
                    containers += '</div><div class="command-use"><b>Parameters :</b><br>{}'.format(out)
            containers += '</div></li>\n'
            if c['type'] == 0:
                cmd_count += 1
            else:
                other_count += 1
        print(cmd_count - prev_count, "slash commands in Cog:", cog, "(total:", cmd_count, ")")
        prev_count = cmd_count
    print("Total:", cmd_count, "slash commands,", other_count, "other commands")
    if cmd_count > 95:
        print("Warning, the number of slash commands might be too high")
    filters += '</div><br><input type="text" id="textSelection" onkeyup="searchSelection()" placeholder="Search a command"><br>\n'
    containers += '</ul>\n'
    commandList = '<div id="Commands" class="tabcontent">' + filters + containers + '</div>\n'
    other_tabs = '''
<div id="Guide" class="tabcontent">
<h1>Guide</h1>
<h2>What is this?</h2>
<p>MizaBOT is a <a href="http://game.granbluefantasy.jp">Granblue Fantasty</a> themed <a href="https://discord.com/">Discord</a> Bot.<br>
It's open source and available on <a href="https://github.com/MizaGBF/MizaBOT">GitHub</a>.<br>
It provides various commands, ranging from utilty to recreative ones, related (or not) to the game.<br></p>

<h2>How to invite?</h2>
<p><b>Invitations are only open to servers of 30 or more people.</b><br>
Here's the invitation link:<br>
<br>
<a href="https://discord.com/api/oauth2/authorize?client_id=614723060100104193&permissions=545394785367&scope=bot%20applications.commands"><img src="img/invite.png"></a><br>
<br>
<b>If the bot leaves your server on its own</b>, it means you don't satisfy the requirements, the invitations are closed OR you or your server has been banned from using the Bot.</p>

<h2>What to do after inviting the bot?</h2>
<p>1) Don't panic if you can't use the bot yet! The commands can take up to one hour to show up.(It's an innate Discord limitation, sadly).<br>
<br>
2A) Make a bot channel if you want. The bot is designed to not post in channels where it doesn't have the "send messages" permission, meaning you can confine it in one channel if you desire to.<br>
<br>
2B) If you still want to use it in other channels, there is an auto clean up system (meaning the command messages will be deleted after a while, to avoid spam). Check out the command /mod cleanup toggle (and its helpers /mod cleanup reset, /mod cleanup see)<br>
<br>
And you are mostly done after this.</p>

<h2>What other features can I enable on my server?</h2>
<p>1) If you are a server for a Granblue Fantasy Crew, you can set your Crew Strike Time with /mod strike set.<br>
Simply give it the hours (JST Timezone).<br>
The command /mod strike del allows you to delete them.<br>
Your Strike Times will appear when using the /gbf info command.</p>

<p>2) You can setup a pinboard with the /mod pinboard enable command. It's not very complicated but here are detailed steps:<br>
First, activate developer mode in your Discord Settings, it will come handy.<br>
Second, go to every channels you want to be able to trigger the pinboard, and copy their ID (with a right click > Copy ID)<br>
Third, put those IDs together in one string, separated by a semi colon (example: 4687977847;84786464;64768468)<br>
Fourth, make a new channel dedicated to it, called pinboard or whatever. Right click on that channel and copy its ID too (Don't put it with the others).<br>
<br>
Now you can do /mod pinboard enable:<br>
tracked_channels will be the string I made you do.<br>
emoji is the emote people must react with to trigger the pin.<br>
threshold is the number of reactions to be reached to trigger the pin.<br>
mod_bypass allows a mod to force the pin just by reacting with that emote. Set it to 1 to enable. It's useful for small or slow servers.<br>
pinning_channel is the ID of the pinboard channel you created.<br>
<br>
You can redo the /mod pinboard enable command to change those settings or use /mod pinboard disable to disable it.<br>
Finally, /mod pinboard see lets you see your current server pinboard settings.</p>

<h2>How do I host my own copy of the Bot?</h2>
<p>First, I wouldn't recommend hosting your own copy. The bot is tailored around my needs and might be problematic to setup.<br>
If you are still interested, the <a href="https://github.com/MizaGBF/MizaBOT/wiki">Github Wiki</a> might help.<br>
It's not always up to date but I keep it updated as much as possible.</p>
</div>
<div id="FAQ" class="tabcontent">
<h1>Frequently Asked Questions / Troubleshooting</h1>
<h2>Does the bot collect my messages/data?</h2>
<p>No. It never did and, since version v9.0, the bot is in fact unable to even see the user messages.</p>

<h2>Can you explain the various command types?</h2>
<p>Slash Commands are used by simply typing / in chat.<br>
User Commands are used by right clicking on an user and going into the Apps context menu.<br>
Message Commands are used by right clicking a message and going into the Apps context menu.</p>

<h2>How do I report a bug?</h2>
<p>Errors are usually automatically reported but, if you found an odd behavior or what seems like an error, you can use the /bug_report command. You can also right click the message and select Apps > Report a Bug to send me that message.</p>

<h2>How do I remove my GBF Profile ID?</h2>
<p>Your linked GBF ID can be removed with the /unsetprofile command.
It's also deleted if you leave all servers where the bot is present.</p>

<h2>How do I remove my set Rolls?</h2>
<p>Your spark data is deleted after 30 days without an update, just leave it alone.</p>

<h2>One or multiple commands don't work</h2>
<p>If none of the commands appear and the bot was in your server <b>BEFORE</b> the v9.0, make sure your server owner refreshed the permissions (He only need to click the invite link and to authorize again, no need to kick the bot).<br>
<br>
If no commands appear when typing /, you might have to wait (it can take up to one hour to register them).<br>
<br>
If you get an "Interaction failed" error, either you tried to use a command without the proper permission (example, a mod command without being mod), you or the bot doesn't have the permission to run this command in this channel, OR the bot is down or rebooting.</p>

<h2>My command froze/hanged</h2>
<p>The bot most likely rebooted during this timeframe, bad luck for you.</p>

<h2>The command didn't register what I set</h2>
<p>Again, the bot most likely rebooted and it didn't save in properly. Just wait and do it again.</p>

<h2>Slash commands suck, how do I get back the old ones?</h2>
<p>Impossible. Blame Discord for pushing this change, not me.</p>
'''

    css = """
<style>
html, body {
  background: #14041c;
  font-family: sans-serif;
  font-size: 16px;
}

h1 {
  text-align: center;
  color: white;
}

h2 {
  color: white;
}

p {
  color: white;
}

a {
  color: #981cd6;
}

a:visited {
  color: #ca1cd6;
}

#textSelection {
  background-image: url('img/searchicon.png');
  background-position: 10px 12px;
  background-repeat: no-repeat;
  width: 100%;
  font-size: 16px;
  padding: 12px 20px 12px 40px;
  border: 1px solid #ddd;
  margin-bottom: 12px;
}

#commandList {
  list-style-type: none;
  padding: 0;
  margin: 0;
}

.command {
  float: left;
  background-color: #101010;
  color: #ffffff;
  width: 100%;
  margin: 2px;
  opacity: 1;
  transition: opacity 0.2s linear;
  display: none; /* Hidden by default */
}

.command:hover {
  background-color: #981cd6;
}

.command-name {
  padding: 10px;
  background: rgba(0, 0, 0, 0.7);
  font-size: 18px;
  font-weight: 700;
}
.command-use {
  padding: 10px;
  background: rgba(0, 0, 0, 0.3);
}
.command-description {
  padding: 10px;
  background: rgba(0, 0, 0, 0.6);
}

.show {
  display: block;
}

.btn {
  border: none;
  outline: none;
  padding: 12px 16px;
  cursor: pointer;
  color: white;
  text-shadow: 2px 2px 2px rgba(0,0,0,0.5);
  margin: 2px;
  font-size: 20px;
}

.btn:hover {
  outline: solid #ca1cd6;
}

.btn.active {
  outline: solid #981cd6;
}

.tab {
  overflow: hidden;
}

/* Style the buttons that are used to open the tab content */
.tablinks {
  border: none;
  outline: none;
  padding: 12px 16px;
  cursor: pointer;
  background: #4f4f4f;
  color: white;
  text-shadow: 2px 2px 2px rgba(0,0,0,0.5);
  margin: 2px;
  border-radius: 10%;
  font-size: 25px;
}

/* Change background color of buttons on hover */
.tablinks:hover {
  background-color: #6f6f6f;
}

/* Create an active/current tablink class */
.tablinks.active {
  background-color: #463254;
}

/* Style the tab content */
.tabcontent {
  display: none;
  padding: 6px 12px;
}
</style>"""
    js = """<script>
function searchSelection(update=true) {
  var input, filter, ul, li, a, i, txtValue;
  input = document.getElementById('textSelection');
  filter = input.value.toUpperCase();
  ul = document.getElementById("commandList");
  li = ul.getElementsByTagName('li');

  for (i = 0; i < li.length; i++) {
    txtValue = li[i].textContent || li[i].innerText;
    if (txtValue.toUpperCase().indexOf(filter) > -1) {
      if(update)
        addClass(li[i], "show");
    } else {
      rmClass(li[i], "show");
    }
  }
}
function filterSelection(c) {
  var x, i;
  x = document.getElementsByClassName("command");
  if (c == "all") c = "";
  for (i = 0; i < x.length; i++) {
    rmClass(x[i], "show");
    if (x[i].className.indexOf(c) > -1) addClass(x[i], "show");
  }
  searchSelection(false);
}

function addClass(element, name) {
  var i, arr1, arr2;
  arr1 = element.className.split(" ");
  arr2 = name.split(" ");
  for (i = 0; i < arr2.length; i++) {
    if (arr1.indexOf(arr2[i]) == -1) {
      element.className += " " + arr2[i];
    }
  }
}

function rmClass(element, name) {
  var i, arr1, arr2;
  arr1 = element.className.split(" ");
  arr2 = name.split(" ");
  for (i = 0; i < arr2.length; i++) {
    while (arr1.indexOf(arr2[i]) > -1) {
      arr1.splice(arr1.indexOf(arr2[i]), 1);
    }
  }
  element.className = arr1.join(" ");
}

var btns = document.getElementsByClassName("btn");
for (var i = 0; i < btns.length; i++) {
  btns[i].addEventListener("click", function() {
    var current = document.getElementsByClassName("btn active");
    current[0].className = current[0].className.replace(" active", "");
    this.className += " active";
  });
}

function openTab(evt, tabName) {
  var i, tabcontent, tablinks;

  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }

  tablinks = document.getElementsByClassName("tablinks");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }

  document.getElementById(tabName).style.display = "block";
  evt.currentTarget.className += " active";
}

filterSelection("all")
</script>"""
    # write the result
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(metadata + '<body>' + header + tabs + commandList + other_tabs + css + js + '</body>')

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
                c['comment'] = tmp.replace("        ", "").replace('\n', '<br>')
            else:
                c['comment'] = ""
            if pos_list[i][1] == 4: # setting up sub_command_group name translation
                if alias is not None:
                    func_index[cog + "_" + base_name] = pos_list[i][2] + " " + c['name']
                else:
                    func_index[cog + "_" + c['name']] = pos_list[i][2] + " " + c['name']
            # IF AND ONLY IF the word "owner" or "hidden" are present in the description, we actually don't store the command
            # for that reason, the word owner shouldn't be used in regular command descriptions
            if 'owner' not in c['comment'].lower() and 'hidden' not in c['comment'].lower():
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

def generate_help(): # main function
    global func_index # dictionnary for translating command groups to their names (IF renamed)
    print("Generating index.html...")
    func_index = {}
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
                                print("Cog", class_name, "found in", p)
                        except Exception as e:
                            print(e)
            except:
                pass
    generate_html(command_list) # generate the html using the stored data on found commands

if __name__ == "__main__": # entry point
    generate_help()