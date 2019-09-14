import discord
from discord.ext import commands
import asyncio
import aiohttp
from datetime import datetime, timedelta
import random

races = {
    'Human': {'humanoid':1, 'gender':1, 'monster':0, 'start_lvl':1, 'base_stat':{'str':[6, 12], 'dex':[6, 12], 'con':[6, 12], 'int':[6, 12], 'wis':[6, 12], 'cha':[6, 12]}, 'stat_grow':{'str':1, 'dex':1, 'con':2, 'int':3, 'wis':2, 'cha':1}, 'startstr':'beghuman'},
    'Elf': {'humanoid':1, 'gender':1, 'monster':0, 'start_lvl':4, 'base_stat':{'str':[6, 10], 'dex':[8, 14], 'con':[6, 10], 'int':[10, 16], 'wis':[10, 18], 'cha':[10, 16]}, 'stat_grow':{'str':1, 'dex':2, 'con':2, 'int':3, 'wis':3, 'cha':1}, 'startstr':'begelf'},
    'Dwarf': {'humanoid':1, 'gender':1, 'monster':0, 'start_lvl':3, 'base_stat':{'str':[9, 12], 'dex':[6, 10], 'con':[10, 14], 'int':[6, 10], 'wis':[7, 14], 'cha':[6, 12]}, 'stat_grow':{'str':2, 'dex':2, 'con':3, 'int':1, 'wis':1, 'cha':1}, 'startstr':'begdwarf'}
}

statNameTable = {
    'str':'Strengh',
    'dex':'Dexterity',
    'con':'Constitution',
    'int':'Intelligence',
    'wis':'Wisdom',
    'cha':'Charm'
}

skillDatabase = {
    'template':{'desc':"For the dev", 'type':'skill type, 0 is a fighting skill, 1 is an usable skill, 2 is a passive skill', 'target':'target of the skill, 0 is self, 1 is single enemy, 2 is group enemy', 'acc':'accuracy in %', 'dmg':'damage type, 0 is raw, 1 is magical, 2 is mixed, 3 is pure', 'pwr':'effiency of the skill', 'wpnprof':'weapon proficiency, 0 is None, 1 is physical weapon, 2 is magical weapon, 3 is both', 'wpn':'weapon requirement, 0 is None, 1 is physical weapon, 2 is magical weapon, 3 is both', 'lvlmax':'level max', 'unlock':'requierement to unlock the skill', 'mod':'stats modifiers'},

    'fight':{'name':"Basic Fighting", 'desc':"Basic and ineficient way to fight", 'type':0, 'target':0, 'acc':90, 'dmg':0, 'pwr':10, 'wpnprof':1, 'wpn':0, 'lvlmax':10, 'unlock':[{'humanoid':1}], 'mod':{'str':0.1, 'dex':0.05, 'cons':0.05}},
    'weapon1':{'name':"Weapon Beginner", 'desc':"Fight hesitantly with a weapon", 'type':0, 'target':0, 'acc':90, 'dmg':0, 'pwr':20, 'wpnprof':1, 'wpn':0, 'lvlmax':10, 'unlock':[{'skills':{'fight':2}, 'wpn':1}], 'mod':{'str':0.1, 'dex':0.05, 'cons':0.05}},
    'weapon2':{'name':"Weapon Intermediary", 'desc':"Fight with a weapon", 'type':0, 'target':0, 'acc':90, 'dmg':0, 'pwr':40, 'wpnprof':1, 'wpn':0, 'lvlmax':10, 'unlock':[{'skills':{'weapon1':10}, 'wpn':1}], 'mod':{'str':0.1, 'dex':0.05, 'cons':0.05}},
    'weapon3':{'name':"Weapon Experimented", 'desc':"Fight efficiently with a weapon", 'type':0, 'target':0, 'acc':95, 'dmg':0, 'pwr':80, 'wpnprof':1, 'wpn':0, 'lvlmax':10, 'unlock':[{'skills':{'weapon2':10}, 'wpn':1}], 'mod':{'str':0.1, 'dex':0.05, 'cons':0.05}}
}

worldDatabase = [
    {
        'name':"Dawn Village",
        'description':"A peaceful village with little danger.\nThe perfect place to start adventuring",
        'quests':[
            {'name':"Medicinal Herb gathering [★]", 'description':"Your mission is to collect medicinal herb at the village outskirts.\nSafe and easy but doesn't pay much.", 'startevent':1, 'duration':20, 'location':'Dawn Village outskirts', 'unlock':{'w0':0}},
            {'name':"Outskirt Night Patrol [★★]", 'description':"Monster sighting at night have been reported to the village guards. We want you to check and eliminate any danger.", 'startevent':0, 'duration':20, 'location':'Dawn Village outskirts', 'unlock':{'test':0}}
        ],
        'travels':[
        ],
        'randarrivalstr':['w0arr0', 'w0arr1', 'w0arr2'],
        'cost':1,
        'shop':[]
    }
]

stringDatabase = {
    'beghuman':"%N arrived today at %w0 and %p0 decided to earn a living by adventuring.\nThis place is peaceful and far from the war, it's perfect for %p1 debut.",
    'begdwarf':"%N arrived after at %w0 and %p0 decided to earn a living by adventuring.\n*(place holder)*",
    'begelf':"%N arrived today at %w0 and %p0 decided to earn a living by adventuring.\n*(place holder)*",
    'w0arr0':"%N is back to %w0 and %p1 memories start to flood in.",
    'w0arr1':"%N arrives finally at %w0 and is impatient to rest a bit.",
    'w0arr2':"%N goes through the gates of %w0, passing some merchants quarrelling with the guards.",
    'w0l0_00':"%N departs from the village, in search for medicinal herbs.",
    'w0l0_01':"%N quickly finds a gathering spot, having knowledge of where the medicinal herbs grow.\nThe place is relatively untouched, %N guesses that people don't usually go here and profits to collect herbs in a perfect condition.\n\nWith a bag full of herbs, %p0 departs as quickly as %p0 arrived.\n\n*(Critical Success)* *(Speed Bonus)*",
    'w0l0_02':"%N quickly finds a gathering spot, having knowledge of where the medicinal herbs grow.\n%P0 starts collecting herbs in a good condition and departs as quickly as %p0 arrived.\n\n*(Good Success)* *(Speed Bonus)*",
    'w0l0_03':"%N find a gathering spot, having knowledge of where the medicinal herbs grow.\nThe place is relatively untouched, %N guesses that people don't usually go here and profits to collect herbs in a perfect condition.\n\nAfter some time, %p0 departs with a bag full of herbs.\n\n*(Critical Success)*",
    'w0l0_04':"%N find a gathering spot, having knowledge of where the medicinal herbs grow.\nAfter taking %p1 time to pick the herbs in a good condition, %N departs with a full bag.\n\n*(Good Success)*",
    'w0l0_05':"%N starts exploring the village outskirts, collecting what %p0 thinks are medicinal herbs.\nAfter a long time, %p0 decides to take back %p1 butin to the guild."
}

genderTable = [
    {None:"It", 0:"He", 1:"She"},
    {None:"Its", 0:"His", 1:"Her"}
]

itemDatabase = {
    'wpn001':{'name':'Wooden Club', 'description':"A cheap but durable club made of wood.", 'price':50, 'type':1, 'pwr':20},
    'wpn002':{'name':'Copper Sword', 'description':"An ordinary sword. Don't expect much from it.", 'price':150, 'type':1, 'pwr':40},
    'wpn003':{'name':'Oak Cane', 'description':"A cane usable to cast magic.", 'price':50, 'type':2, 'pwr':50},
    'arm001':{'name':'Leather Vest', 'description':"Lite but doesn't offer much protection.", 'price':50, 'type':1, 'pwr':20},
    'arm002':{'name':'Copper Chainmail', 'description':"Simple but durable chainmail made of copper.", 'price':50, 'type':2, 'pwr':30}
}

monsterDatabase = {
    "000" : {'name':"Test Dummy", 'hp':50, 'atk':10, 'type':0, 'pdef':10.0, 'mdef':5.0, 'gold':5, 'exp':5, 'loot':[], 'winactions':[], 'loseactions':[]}
}


class RPG(commands.Cog):
    """RPG (beta)."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x5bc69b
        self.version = 'MizaBOT RPG ▪ v0.1'
        self.rpg = {} # save data placeholder


    def startTasks(self):
        self.bot.runTask('rpgtask', self.rpgtask)

    async def rpgtask(self): #TODO
        await asyncio.sleep(2)
        await self.bot.send('debug', embed=self.bot.buildEmbed(title="rpgtask() started", timestamp=datetime.utcnow()))
        while True:
            if self.bot.exit_flag: return
            await asyncio.sleep(120)
            c = self.bot.getJST()
            for id in self.rpg:
                character = self.rpg[id]
                if character['action'] == 'quest':
                    if c >= character['cooldown'] + timedelta(seconds=60*character['duration']):
                        await self.playEvent(id)
            try:
                pass
            except asyncio.CancelledError:
                await self.bot.sendError('rpgtask', 'cancelled')
                return
            except Exception as e:
                await self.bot.sendError('rpgtask', str(e))

    def isOwner(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isOwner(ctx)
        return commands.check(predicate)

    def updatePlayerChannel(self, ctx):
        if str(ctx.author.id) in self.rpg and ctx.channel.id != self.rpg[str(ctx.author.id)]['channel']:
            self.rpg[str(ctx.author.id)]['channel'] = ctx.channel.id
            #self.bot.savePending = True

    def processString(self, key, character):
        if key not in stringDatabase: return "Error"
        text = stringDatabase[key]
        text = text.replace("%n", character['name'].lower()).replace("%N", character['name']).replace("%P0", genderTable[0][character.get('gender', None)]).replace("%p0", genderTable[0][character.get('gender', None)].lower()).replace("%P1", genderTable[1][character.get('gender', None)]).replace("%p1", genderTable[1][character.get('gender', None)].lower())
        for i in range(0, len(worldDatabase)):
            text = text.replace("%w"+str(i), worldDatabase[i]['name'])
            for j in range(0, len(worldDatabase[i]['quests'])):
                text = text.replace("%q" + str(j) + "w"+str(i), worldDatabase[i]['quests'][j]['name'])
                text = text.replace("%l" + str(j) + "w"+str(i), worldDatabase[i]['quests'][j]['location'])
        return text

    def changeQuestState(self, id, quest, state):
        if self.rpg[id]['action'] == "dead": return
        self.rpg[id]['action'] = state
        self.rpg[id]['cooldown'] = self.bot.getJST()
        self.rpg[id]['quest'] = quest
        #self.bot.savePending = True

    def charAtkPower(self, character): # TODO
        skid = 'fight'
        if character['equip']['skill'] is not None: skid = character['equip']['skill']
        sk = skillDatabase[skid]
        pwr = sk['pwr'] * sk
        # weapon prof check
        if sk['wpn'] != 0:
            wpnid = character['equip']['weapon']
            if wpnid is None: pwr = pwr * 0.75
            else:
                wpn = itemDatabase[wpnid]
                if sk['wpn'] != wpn['type']:
                    pwr = pwr * 0.75
        # stat mod
        for stat in sk['mod']:
            pwr += character[stat] * sk['mod'][stat]
        return [pwr, sk['dmg']]

    def charDefRating(self, character): # TODO
        pdef = 2.8 + character['lvl'] * 0.2 + character['str'] * 0.05 + character['con'] * 0.2
        mdef = 2.8 + character['lvl'] * 0.1 + character['int'] * 0.1 + character['wis'] * 0.1       
        return [pdef, mdef]

    def battle(self, cid, mid):
        character = self.rpg[cid]
        mob = monsterDatabase[mid]
        mhp = mob['hp']
        log = "Battle with {}\n\n".format(mob['name'])
        stats = {'nstrike':[0, 0], 'starthp':[mhp, character['hp']]}
        while character['hp'] > 0 and mhp > 0:
            catk = self.charAtkPower(character)
            if catk[1] == 0:
                mhp -= catk[0] / mob['pdef']
            elif catk[1] == 1:
                mhp -= catk[0] / mob['mdef']
            elif catk[1] == 2:
                mhp -= (catk[0] / mob['pdef'] + catk[0] / mob['mdef'])
            elif catk[1] == 3:
                mhp -= catk[0]
            mhp = round(mhp)
            stats['nstrike'][0] += 1
            if mhp <= 0: break

            cdef = self.charDefRating(character)
            if mob['type'] == 0:
                character['hp'] -= mob['atk'] / cdef[0]
            elif mob['type'] == 1:
                character['hp'] -= mob['atk'] / cdef[1]
            elif mob['type'] == 2:
                character['hp'] -= (mob['atk'] / cdef[0] + mob['atk'] / cdef[1])
            elif mob['type'] == 3:
                character['hp'] -= mob['atk']
            character['hp'] = round(character['hp'])
            stats['nstrike'][1] += 1
        if mhp < 0:
            ratio = character['hp'] / (stats['starthp'][1] * 1.0)
            if ratio <= 0.1: log += "{} barely survives the {}\n".format(character['name'], random.choice(['fight', 'battle', 'encounter', 'confrontation']))
            elif ratio <= 0.3: log += "{} isn't in a good shape after this {}\n".format(character['name'], random.choice(['fight', 'battle', 'encounter', 'confrontation']))
            elif ratio <= 0.6: log += "{} took some damage during the {}\n".format(character['name'], random.choice(['fight', 'battle', 'encounter', 'confrontation']))
            elif ratio <= 0.8: log += "{} did pretty well during this {}\n".format(character['name'], random.choice(['fight', 'battle', 'encounter', 'confrontation']))
            else: log += "{} barely broke a sweat during this {}\n".format(character['name'], random.choice(['fight', 'battle', 'encounter', 'confrontation']))
            if stats['nstrike'][1] == 1: log += "One strike was all it took to kill {}\n".format(mob['name'])
            elif stats['nstrike'][1] < 4: log += "Just a few exchange of blows were enough to end {}'s life\n".format(mob['name'])
            elif stats['nstrike'][1] < 10: log += "The battle with {} ended relatively fast\n".format(mob['name'])
            elif stats['nstrike'][1] < 20: log += "{} was resistant, the battle didn't end easily\n".format(mob['name'])
            elif stats['nstrike'][1] < 40: log += "A long battle with {} took place\n".format(mob['name'])
            elif stats['nstrike'][1] < 20: log += "It was an endurance battle\n".format(mob['name'])
        else:
            log += "You died (TODO)\n"
            character['action'] = 'dead'
        self.rpg[cid] = character
        #self.bot.savePending = True
        return log

    async def processAction(self, ctx, character): #TODO
        action = character['action']
        if action == 'dead':
            await ctx.send(embed=self.bot.buildEmbed(title="Dead", description="To do", footer=self.version, color=self.color))
            return False
        elif action == 'travel':
            self.rpg[str(ctx.author.id)]['action'] = 'idle'
            #self.bot.savePending = True
            await ctx.send(embed=self.bot.buildEmbed(title="Arrived at destination", description="To do", footer=self.version, color=self.color))
        elif action == 'quest':
            await ctx.send(embed=self.bot.buildEmbed(title="Quest", description="To do", footer=self.version, color=self.color))
        return True

    async def send(self, dest, mention, embed, mention_flag):
        try:
            if mention_flag:
                await dest.send(content=mention, embed=embed)
            else:
                await dest.send(content=mention, embed=embed)
        except Exception as e:
            await self.bot.sendError('rpg send', str(e))

    async def checkUnlock(self, character, ctx = None): #TODO
        for s in skillDatabase:
            if s is 'template': continue
            if s in character['skills']: continue
            unlock = skillDatabase[s]['unlock']
            for check in unlock:
                confirmed = True
                if 'skills' in check:
                    for x in check['skills']:
                        if x not in character['skills'] or character['skills'][x] < check['skills'][x]:
                            confirmed = False
                            break
                if 'humanoid' in check:
                    if races[character['race']]['humanoid'] != check['humanoid']:
                        confirmed = False
                if 'wpn' in check:
                    confirmed = False
                if confirmed:
                    character['skills'][s] = 1
                    if not ctx is None:
                        await ctx.send(embed=self.bot.buildEmbed(title=character['name'] + " - Skill Unlock", description=skillDatabase[s]['name'], footer=self.version, color=self.color))
                    break
        return character

    @commands.command(no_pm=True)
    @isOwner()
    async def ghelp(self, ctx):
        await ctx.send(embed=self.bot.buildEmbed(title=self.version + " ▪ Help", description="gstart ▪ Create a character\ngstatus ▪ Open your character status", color=self.color))

    @commands.command(no_pm=True) # TODO HP!!!
    @isOwner()
    async def gstart(self, ctx, *, name: str = ""):
        """WIP"""
        if str(ctx.author.id) in self.rpg:
            await ctx.send(embed=self.bot.buildEmbed(title="You already have a character", description="<error>", footer=self.version, color=self.color))
        else:
            starting_races = ['Human', 'Elf', 'Dwarf']
            if name == "": name = ctx.author.display_name
            character = {'name':name, 'race':random.choice(starting_races), 'skills':{}, 'cooldown':self.bot.getJST(), 'duration':0, 'current':{'world':0, 'level':0}, 'action':'idle', 'channel':0, 'questvar':{}, 'quest':0, 'inv':[], 'equip':{'skill':None, 'weapon':None, 'armor':None, 'extra':None}, 'flags':{'w0':0}}
            chara_race = races[character['race']]
            character['lvl'] = chara_race['start_lvl']
            if 'gender' in chara_race:
                character['gender'] = random.randint(0, 1)
            for s in chara_race['base_stat']:
                character[s] = random.randint(chara_race['base_stat'][s][0]*10, chara_race['base_stat'][s][1]*10) / 10.0
            character = await self.checkUnlock(character)
            self.rpg[str(ctx.author.id)] = character
            #self.bot.savePending = True
            self.updatePlayerChannel(ctx)
            await ctx.send(embed=self.bot.buildEmbed(title=character['name'] + " has been created", description=self.processString(chara_race['startstr'], character), footer=self.version, color=self.color))
            await self.bot.callCommand(ctx, 'gstatus', 'RPG')

    @commands.command(no_pm=True)
    @isOwner()
    async def gstatus(self, ctx):
        """WIP"""
        if str(ctx.author.id) not in self.rpg:
            await ctx.send(embed=self.bot.buildEmbed(title="Please create a character first", description="command: `gstart [your name]`", footer=self.version, color=self.color))
        else:
            self.updatePlayerChannel(ctx)
            character = self.rpg[str(ctx.author.id)]
            desc = character['race']
            if 'gender' in character:
                if character['gender'] == 0: desc += ", Male\n"
                else: desc += ", Female\n"
            else:
                desc += "\n"
            desc += "Level: " + str(character['lvl']) + "\n"
            if character['action'] == 'idle': desc += "Located at " + worldDatabase[character['current']['world']]['name']
            elif character['action'] == 'travel': desc += "Traveling to " + worldDatabase[character['current']['world']]['name']

            fields = [{'name':'Stats', 'value':""}, {'name':'Equipment', 'value':""}]

            for s in statNameTable:
                fields[0]['value'] += statNameTable[s] + ": " + str(character[s]) + "\n"
            if len(character['skills']) > 0:
                fields[0]['value'] += str(len(character['skills'])) + " skill(s)"

            if character['equip']['weapon'] is None: fields[1]['value'] += "Weapon: None\n"
            else: fields[1]['value'] += "Weapon: " + itemDatabase[character['equip']['weapon']]['name'] + "\n"
            if character['equip']['armor'] is None: fields[1]['value'] += "Armor: None\n"
            else: fields[1]['value'] += "Armor: " + itemDatabase[character['equip']['armor']]['name'] + "\n"
            if character['equip']['extra'] is None: fields[1]['value'] += "Accessory: None\n"
            else: fields[1]['value'] += "Accessory: " + itemDatabase[character['equip']['extra']]['name'] + "\n"

            await ctx.send(embed=self.bot.buildEmbed(title=character['name'], description=desc, fields=fields, inline=True, footer=self.version, color=self.color))

    @commands.command(no_pm=True)
    @isOwner()
    async def gequip(self, ctx, name : str):
        """WIP"""
        pass

    @commands.command(no_pm=True)
    @isOwner()
    async def gadventure(self, ctx, quest : int = -1):
        """WIP"""
        c = self.bot.getJST()
        character = self.rpg.get(str(ctx.author.id), None)
        self.updatePlayerChannel(ctx)

        if character is None:
            await ctx.send(embed=self.bot.buildEmbed(title="Please create a character first", description="command: `gstart [your name]`", footer=self.version, color=self.color))
            return
        elif character['action'] != 'idle':
            await ctx.send(embed=self.bot.buildEmbed(title="Your character is adventuring, be patient!", footer=self.version, color=self.color))
            return

        current = character['current']
        world = worldDatabase[current['world']]
        choices = []
        for i in range(0, len(world['quests'])):
            unlocked = True
            for u in world['quests'][i]['unlock']:
                if u not in character['flags'] or character['flags'][u] < world['quests'][i]['unlock'][u]:
                    unlocked = False
                    break
            if unlocked:
                choices.append({'name':world['quests'][i]['name'], 'type':0, 'id':i})

        
        for i in range(0, len(world['travels'])):
            unlocked = True
            for u in world['travels'][i]['unlock']:
                if u not in character['flags'] or character['flags'][u] < world['travels'][i]['unlock'][u]:
                    unlocked = False
                    break
            if unlocked:
                choices.append({'name':"Travel to " + worldDatabase[world['travels'][i]['id']]['name'], 'type':1, 'id':i})

        if quest < 0 or quest >= len(choices):
            msg = ""
            for i in range(0, len(choices)):
                msg += "[" + str(i) + "] " + choices[i]['name'] + "\n"
            await ctx.send(embed=self.bot.buildEmbed(title="Please select a destination", description=msg, footer=self.version, color=self.color))
        else:
            ch = choices[quest]
            if ch['type'] == 0:
                self.rpg[str(ctx.author.id)]['action'] = 'quest'
                self.rpg[str(ctx.author.id)]['current']['level'] = ch['id']
                self.rpg[str(ctx.author.id)]['cooldown'] = c
                self.rpg[str(ctx.author.id)]['duration'] = world['quests'][ch['id']]['duration']
                self.rpg[str(ctx.author.id)]['quest'] = world['quests'][ch['id']]['startevent']
                #self.bot.savePending = True
                await self.playEvent(str(ctx.author.id))
            elif ch['type'] == 1:
                self.rpg[str(ctx.author.id)]['action'] = 'travel'
                self.rpg[str(ctx.author.id)]['current']['world'] = ch['id']
                self.rpg[str(ctx.author.id)]['cooldown'] = c
                self.rpg[str(ctx.author.id)]['duration'] = 60
                #self.bot.savePending = True
                await ctx.send(embed=self.bot.buildEmbed(title="Traveling", description="TODO", footer=self.version, color=self.color))

    async def playEvent(self, id): # TODO
        character = self.rpg.get(id, None)
        if character is None: return
        u = self.bot.get_user(int(id))
        if u is None: return
        c = self.bot.get_channel(character['channel']) # CHECK
        if c is None: c = u
        ev = character['quest']

        if ev == 0:
            self.changeQuestState(id, 0, 'idle')
        elif ev == 1:
            await c.send(embed=self.bot.buildEmbed(title=character['name'] + " ▪ Quest Event", description=self.processString('w0l0_00', character), footer=self.version, color=self.color))
            r = random.randint(0, 100)
            if r < 10: self.changeQuestState(id, 3, 'quest') # TODO
            else: self.changeQuestState(id, 2, 'quest')
        elif ev == 2:
            self.changeQuestState(id, 4, 'quest')
            if character['int'] >= 12:
                if random.randint(0, 100) < 20 or character['race'] == 'Elf':
                    await c.send(content=u.mention, embed=self.bot.buildEmbed(title=character['name'] + " ▪ Quest Event", description=self.processString('w0l0_01', character), footer=self.version, color=self.color))
                    self.rpg[id]['questvar']['success'] = 3
                    self.rpg[id]['cooldown'] = self.rpg[id]['cooldown'] - timedelta(seconds=1000)
                    #self.bot.savePending = True
                else:
                    await c.send(content=u.mention, embed=self.bot.buildEmbed(title=character['name'] + " ▪ Quest Event", description=self.processString('w0l0_02', character), footer=self.version, color=self.color))
                    self.rpg[id]['questvar']['success'] = 2
                    self.rpg[id]['cooldown'] = self.rpg[id]['cooldown'] - timedelta(seconds=1000)
                    #self.bot.savePending = True
            elif character['int'] >= 10:
                if random.randint(0, 100) < 5 or character['race'] == 'Elf':
                    await c.send(content=u.mention, embed=self.bot.buildEmbed(title=character['name'] + " ▪ Quest Event", description=self.processString('w0l0_03', character), footer=self.version, color=self.color))
                    self.rpg[id]['questvar']['success'] = 3
                    #self.bot.savePending = True
                else:
                    await c.send(content=u.mention, embed=self.bot.buildEmbed(title=character['name'] + " ▪ Quest Event", description=self.processString('w0l0_04', character), footer=self.version, color=self.color))
                    self.rpg[id]['questvar']['success'] = 2
                    #self.bot.savePending = True
            else:
                await c.send(content=u.mention, embed=self.bot.buildEmbed(title=character['name'] + " ▪ Quest Event", description=self.processString('w0l0_05', character), footer=self.version, color=self.color))
                self.rpg[id]['questvar']['success'] = 1
                #self.bot.savePending = True
        elif ev == 3:
            await c.send(content=u.mention, embed=self.bot.buildEmbed(title=character['name'] + " ▪ Quest Event", description=self.battle(id, "000"), footer=self.version, color=self.color))
            self.changeQuestState(id, 4, 'quest')
        elif ev == 4:
            await c.send(content=u.mention, embed=self.bot.buildEmbed(title=character['name'] + " ▪ Quest Event", description="OK", footer=self.version, color=self.color))
            self.changeQuestState(id, 0, 'idle')
'''
Notes:

whenever:
gstatus to see your status
gskill to inspect skills
granking to see the server ranking

out of adventure:
gshop to shop using the earned gold
gequip to equip a weapon or armor
gsetskill to set the fighting skill
gvisit to explore the town and maybe unlock some events

in adventure:
gprogress to see the progress (time left, etc)
gnotification to see your notifications



'''
