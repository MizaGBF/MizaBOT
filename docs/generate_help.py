import os
import re

def find_command_pos(data):
    pos_list = []
    cur = 0
    while True:
        pos = data.find('@commands.command', cur)
        if pos == -1:
            break
        else:
            pos_list.append(pos)
            cur = pos + 1
    return pos_list

def search_interval(data, pos, max_pos, start, end):
    s = data.find(start, pos, max_pos)
    if s == -1: return None
    e = data.find(end, s+len(start), max_pos)
    if e == -1: return None
    return data[s+len(start):e]

def retrieve_command_list(data, pos_list):
    cl = []
    i = data.find('self.color = 0x')
    if i != -1:
        color = data[i+len('self.color = 0x'):i+len('self.color = 0x')+6]
    else:
        color = None
    for i in range(len(pos_list)):
        pos = pos_list[i]
        if i == len(pos_list) - 1:
            fp = data.find(' def ', pos)
            max_pos = len(data) - 1
        else:
            fp = data.find(' def ', pos, pos_list[i+1])
            max_pos = pos_list[i+1]
        if fp != -1:
            c = {'aliases':[]}
            tmp = search_interval(data, pos, max_pos, 'aliases=[', ']')
            if tmp is not None:
                c['aliases'] = tmp.replace('"', '').replace("'", "").split(', ')
            fp += 5
            c['name'] = search_interval(data, pos, max_pos, ' def ', '(') # add search for name
            if c['name'] is None: continue
            if c['name'].startswith('_'): c['name'] = c['name'][1:]
            args = search_interval(data, fp, max_pos, '(', ')')
            args = args.split(', ')
            args.pop(0)
            args.pop(0)
            c['args'] = args
            tmp = search_interval(data, fp, max_pos, '"""', '"""')
            if tmp is not None:
                c['comment'] = tmp.replace("        ", "").replace('\n', '<br>')
            else:
                c['comment'] = ""
            if 'owner' not in c['comment'].lower():
                c['color'] = color
                cl.append(c)
    return cl

def make_name(n, aliases):
    s = n
    for a in aliases:
        s += ', ' + a
    return s

def make_parameters(name, args):
    msg = ""
    sflag = False
    for a in args:
        if a == '*':
            sflag = True
            continue
        if a.startswith('*'):
            a = a[1:]
            sflag = True
        sa = a.split(' : ')
        if len(sa) == 2:
            msg += sa[0]
            ssa = sa[1].split(' = ')
            if len(ssa) == 2:
                at = ssa[0]
                ad = ssa[1]
            else:
                at = sa[1]
                ad = None
            if at == "int": msg += " (Integer)"
            elif at == "str":
                msg += " (String"
                if sflag: msg += "(s) "
                msg += ")"
            elif at == "int": msg += " (Integer)"
            elif at == "discord.Member": msg += " (Member)"
        else:
            ssa = a.split(' = ')
            if len(ssa) == 2:
                msg += ssa[0]
                ad = ssa[1]
            else:
                msg += a
                ad = None
        if ad is not None and ad != '""':
            msg += "(default: {})".format(ad)
        msg += ", "
    if msg == "":
        return '$' + name
    else:
        return '$' + name + ' ' + msg[:-2]

def get_version():
    with open("../bot.py", "r", encoding="utf-8") as f:
        data = f.read()
    return search_interval(data, 0, len(data)-1, 'self.version = "', '"')

def generate_html(command_list):
    header = '<title>MizaBOT Online Command List</title><h1 style="width:630px;margin-left: auto; margin-right: auto;"><img src="img/icon.png" style="vertical-align:middle;border-radius: 50%;box-shadow: 0 0 0 2pt #981cd6">&nbsp;MizaBOT Online Command List<br><small>v{}</small></h1><br>'.format(get_version())
    tabs = '''<div class="tab">
        <button class="tablinks" onclick="openTab(event, 'Commands')">Commands</button>
        <button class="tablinks" onclick="openTab(event, 'About')">About</button>
    </div>'''
    filters = '<div id="buttons"><button class="btn active" onclick="filterSelection(\'all\')" style="background: #050505;">All</button>'
    containers = '<ul id="commandList">'
    for cog in command_list:
        commands = command_list[cog]
        if len(commands) == 0: continue
        filters += '<button class="btn" onclick="filterSelection(\'{}\')" style="background: #{};">{}</button>'.format(cog.lower(), commands[0].get('color', '615d5d'), cog)
        for c in commands:
            containers += '<li class="command {}"><div class="command-name"><span style="display: inline-block;background: #{};padding: 5px;text-shadow: 2px 2px 2px rgba(0,0,0,0.5);">{}</span>&nbsp;&nbsp;{}</div><div class="command-use">{}</div><div class="command-description">{}</div></li>'.format(cog.lower(), c.get('color', '615d5d'), cog, make_name(c['name'], c['aliases']), make_parameters(c['name'], c['args']), c['comment'].replace('(Mod Only)', '<b>(Mod Only)</b>').replace('((You) Mod Only)', '<b>((You) Mod Only)</b>').replace('(NSFW channels Only)', '<b>(NSFW channels Only)</b>'))
    filters += '</div><br><input type="text" id="textSelection" onkeyup="searchSelection()" placeholder="Search a command"><br>'
    containers += '</ul>'
    commandList = '<div id="Commands" class="tabcontent">' + filters + containers + '</div>'
    about = '''
    <div id="About" class="tabcontent">
    <h2>Presentation</h2>
    <p>
    MizaBOT is a <a href="http://game.granbluefantasy.jp">Granblue Fantasty</a> themed <a href="https://discord.com/">Discord</a> Bot.<br>
    It's open source and available on <a href="https://github.com/MizaGBF/MizaBOT">GitHub</a>.<br>
    It provides various commands, ranging from utilty to recreative ones.<br>
    The official version isn't currently open to public invites.<br>
    If you are in a /gbfg/ crew, contact the author directly for an invite.<br>
    </p>
    <h2>Privacy</h2>
    <p>
    The bot doesn't log/register any data related to you or your server beside:<br>
    1) Your GBF ID if set using the <b>setProfile</b> command (It's deleted if you leave all servers where the bot is present or using the <b>unsetProfile</b> command).<br>
    2) Your spark data if set using the <b>setRoll</b> command (It's deleted after 30 days without an update).<br>
    3) Your Discord ID when reporting a bug using the <b>bugreport</b> command (for contacting you, if needed).<br>
    4) Your Discord ID, the channel name, the server name and the command used when a critical error is triggered.<br>
    </p>
    </div>
    '''
    css = """<style>
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
    with open("index.html", "w", encoding="utf-8") as f:
        f.write('<head><link rel="icon" type="image/png" href="img/icon.png" /></head><body>' + header + tabs + commandList + about + css + js + '</body>')

def load():
    r = re.compile("^class ([a-zA-Z0-9_]*)\\(commands\\.Cog\\):", re.MULTILINE)
    command_list = {'Help':[{'name':'Help', 'aliases':[], 'args':['command_name_or_cog : str = ""'], 'comment':'The Bot help command'}]}
    for f in os.listdir('../cogs/'): # list all files
        p = os.path.join('../cogs/', f)
        if f not in ['__init__.py'] and f.endswith('.py') and os.path.isfile(p): # search for valid python file
            try:
                with open(p, mode='r', encoding='utf-8') as py:
                    data = str(py.read())
                    all = r.findall(data) 
                    for group in all:
                        try:
                            class_name = group # the cog Class name
                            cl = retrieve_command_list(data, find_command_pos(data))
                            if len(cl) > 0: command_list[class_name] = cl
                        except Exception as e:
                            print(e)
            except:
                pass
    generate_html(command_list)

load()