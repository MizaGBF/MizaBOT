from discord.ext import commands
import asyncio
import random
from collections import defaultdict
from datetime import datetime, timedelta

# ----------------------------------------------------------------------------------------------------------------
# Casino Cog
# ----------------------------------------------------------------------------------------------------------------
# Mini Discord Card Game commands
# ----------------------------------------------------------------------------------------------------------------

class Casino(commands.Cog):
    """Casino games."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xe3d217
        self.pokergames = {}
        self.blackjackgames = {}

    def value2head(self, value):
        return str(value).replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A")

    def valueNsuit2head(self, value):
        return str(value).replace("D", "\♦️").replace("S", "\♠️").replace("H", "\♥️").replace("C", "\♣️").replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A")

    def checkPokerHand(self, hand): # check hand strengh and return a string indicating its value
        flush = False
        # flush detection
        suits = [h[-1] for h in hand]
        if len(set(suits)) == 1: flush = True
        # other checks
        values = [i[:-1] for i in hand] # get card values
        value_counts = defaultdict(lambda:0)
        for v in values:
            value_counts[v] += 1 # count each match
        rank_values = [int(i) for i in values] # rank them
        value_range = max(rank_values) - min(rank_values) # and get the difference
        # determinate hand from their
        if flush and set(values) == set(["10", "11", "12", "13", "14"]): return "**Royal Straight Flush**"
        elif flush and ((len(set(value_counts.values())) == 1 and (value_range==4)) or set(values) == set(["14", "2", "3", "4", "5"])): return "**Straight Flush, high {}**".format(self.value2head(self.highestCardStripped(list(value_counts.keys()))))
        elif sorted(value_counts.values()) == [1,4]: return "**Four of a Kind of {}**".format(self.value2head(list(value_counts.keys())[list(value_counts.values()).index(4)]))
        elif sorted(value_counts.values()) == [2,3]: return "**Full House, high {}**".format(self.value2head(list(value_counts.keys())[list(value_counts.values()).index(3)]))
        elif flush: return "**Flush**"
        elif (len(set(value_counts.values())) == 1 and (value_range==4)) or set(values) == set(["14", "2", "3", "4", "5"]): return "**Straight, high {}**".format(self.value2head(self.highestCardStripped(list(value_counts.keys()))))
        elif set(value_counts.values()) == set([3,1]): return "**Three of a Kind of {}**".format(self.value2head(list(value_counts.keys())[list(value_counts.values()).index(3)]))
        elif sorted(value_counts.values())==[1,2,2]:
            k = list(value_counts.keys())
            k.pop(list(value_counts.values()).index(1))
            return "**Two Pairs, high {}**".format(self.value2head(self.highestCardStripped(k)))
        elif 2 in value_counts.values(): return "**Pair of {}**".format(self.value2head(list(value_counts.keys())[list(value_counts.values()).index(2)]))
        else: return "**Highest card is {}**".format(self.value2head(self.highestCard(hand).replace("D", "\♦️").replace("S", "\♠️").replace("H", "\♥️").replace("C", "\♣️")))

    def highestCardStripped(self, selection): # return the highest card
        ic = [int(i) for i in selection] # convert to int
        return str(sorted(ic)[-1]) # sort and then convert back to str

    def highestCard(self, selection):
        for i in range(0, len(selection)): selection[i] = '0'+selection[i] if len(selection[i]) == 2 else selection[i]
        last = sorted(selection)[-1]
        if last[0] == '0': last = last[1:]
        return last

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(15, 30, commands.BucketType.guild)
    async def deal(self, ctx):
        """Deal a random poker hand"""
        hand = []
        while len(hand) < 5:
            card = str(random.randint(2, 14)) + random.choice(["D", "S", "H", "C"])
            if card not in hand:
                hand.append(card)
        final_msg = await ctx.reply(embed=self.bot.util.embed(author={'name':"{}'s hand".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description="🎴, 🎴, 🎴, 🎴, 🎴", color=self.color))
        for x in range(0, 5):
            await asyncio.sleep(1)
            # check result
            msg = ""
            for i in range(len(hand)):
                if i > x: msg += "🎴"
                else: msg += self.valueNsuit2head(hand[i])
                if i < 4: msg += ", "
                else: msg += "\n"
            if x == 4:
                await asyncio.sleep(2)
                msg += await self.bot.do(self.checkPokerHand, hand)
            await final_msg.edit(embed=self.bot.util.embed(author={'name':"{}'s hand".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color))
        await self.bot.util.clean(ctx, final_msg, 45)

    def pokerNameStrip(self, name):
        if len(name) > 10:
            if len(name.split(" ")[0]) < 10: return name.split(" ")[0]
            else: return name[:9] + "…"
        return name

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(10, 30, commands.BucketType.guild)
    async def poker(self, ctx):
        """Play a poker mini-game with other people"""
        # search game
        id = ctx.channel.id
        if id in self.pokergames:
            if self.pokergames[id]['state'] == 'waiting':
                if len(self.pokergames[id]['players']) >= 6:
                    await self.bot.util.clean(ctx, (await ctx.reply(embed=self.bot.util.embed(title="Error", description="This game is full", color=self.color))), 6)
                elif ctx.author.id not in self.pokergames[id]['players']:
                    self.pokergames[id]['players'].append(ctx.author.id)
                    await self.bot.util.react(ctx.message, '✅') # white check mark
                else:
                    await self.bot.util.clean(ctx, (await ctx.reply(embed=self.bot.util.embed(title="Error", description="You are already in the next game", color=self.color))), 10)
            else:
                await self.bot.util.clean(ctx, (await ctx.reply(embed=self.bot.util.embed(title="Error", description="This game started", color=self.color))), 10)
        else:
            self.pokergames[id] = {'state':'waiting', 'players':[ctx.author.id]}
            msg = await ctx.reply(embed=self.bot.util.embed(title="♠️ Multiplayer Poker ♥️", description="Starting in 30s\n1/6 players", footer="Use the poker command to join", color=self.color))
            timer = self.bot.util.JST() + timedelta(seconds=30)
            while True:
                await asyncio.sleep(1)
                c = self.bot.util.JST()
                if c >= timer: break
                if len(self.pokergames[id]['players']) >= 6:
                    break
                await msg.edit(embed=self.bot.util.embed(title="♠️ Multiplayer Poker ♥️", description="Starting in {}s\n{}/6 players".format((timer - c).seconds, len(self.pokergames[id]['players'])), footer="Use the poker command to join", color=self.color))
            self.pokergames[id]['state'] = "playing"
            if len(self.pokergames[id]['players']) > 6: self.pokergames[id]['players'] = self.pokergames[id]['players'][:6]
            await self.bot.util.clean(ctx, msg, 0, True)
            # game start
            draws = []
            final_msg = None
            while len(draws) < 3 + 2 * len(self.pokergames[id]['players']):
                card = str(random.randint(2, 14)) + random.choice(["D", "S", "H", "C"])
                if card not in draws:
                    draws.append(card)
            for s in range(-1, 5):
                msg = ":spy: Dealer \▫️ "
                n = s - 2
                for j in range(0, 3):
                    if j > n: msg += "🎴"
                    else: msg += self.valueNsuit2head(draws[j])
                    if j < 2: msg += ", "
                    else: msg += "\n"
                n = max(1, s)
                for x in range(0, len(self.pokergames[id]['players'])):
                    pid = self.pokergames[id]['players'][x]
                    msg += "{} {} \▫️ ".format(self.bot.emote.get(str(x+1)), self.pokerNameStrip(ctx.guild.get_member(pid).display_name))
                    if s == 4:
                        highest = self.highestCard(draws[3+2*x:5+2*x])
                    for j in range(0, 2):
                        if j > s: msg += "🎴"
                        elif s == 4 and draws[3+j+2*x] == highest: msg += "__" + self.valueNsuit2head(draws[3+j+2*x]) + "__"
                        else: msg += self.valueNsuit2head(draws[3+j+2*x])
                        if j == 0: msg += ", "
                        else:
                            if s == 4:
                                msg += " \▫️ "
                                hand = draws[0:3] + draws[3+2*x:5+2*x]
                                hstr = await self.bot.do(self.checkPokerHand, hand)
                                if hstr.startswith("**Highest"):
                                    msg += "**Highest card is {}**".format(self.valueNsuit2head(self.highestCard(draws[3+2*x:5+2*x])))
                                else:
                                    msg += hstr
                            msg += "\n"
                if final_msg is None: final_msg = await ctx.reply(embed=self.bot.util.embed(title="♠️ Multiplayer Poker ♥️", description=msg, color=self.color))
                else: await final_msg.edit(embed=self.bot.util.embed(title="♠️ Multiplayer Poker ♥️", description=msg, color=self.color))
                await asyncio.sleep(2)
            self.pokergames.pop(id)
            await self.bot.util.clean(ctx, final_msg, 45)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(10, 30, commands.BucketType.guild)
    async def blackjack(self, ctx):
        """Play a blackjack mini-game with other people"""
        # search game
        id = ctx.channel.id
        if id in self.blackjackgames:
            if self.blackjackgames[id]['state'] == 'waiting':
                if len(self.blackjackgames[id]['players']) >= 6:
                    await self.bot.util.clean(ctx, (await ctx.reply(embed=self.bot.util.embed(title="Error", description="This game is full", color=self.color))), 6)
                elif ctx.author.id not in self.blackjackgames[id]['players']:
                    self.blackjackgames[id]['players'].append(ctx.author.id)
                    await self.bot.util.react(ctx.message, '✅') # white check mark
                else:
                    await self.bot.util.clean(ctx, (await ctx.reply(embed=self.bot.util.embed(title="Error", description="You are already in the next game", color=self.color))), 10)
            else:
                await self.bot.util.clean(ctx, (await ctx.reply(embed=self.bot.util.embed(title="Error", description="This game started", color=self.color))), 10)
        else:
            self.blackjackgames[id] = {'state':'waiting', 'players':[ctx.author.id]}
            msg = await ctx.reply(embed=self.bot.util.embed(title="♠️ Multiplayer Blackjack ♥️", description="Starting in 30s\n1/6 players", footer="Use the blackjack command to join", color=self.color))
            timer = self.bot.util.JST() + timedelta(seconds=30)
            while True:
                await asyncio.sleep(1)
                c = self.bot.util.JST()
                if c >= timer: break
                if len(self.blackjackgames[id]['players']) >= 6:
                    break
                await msg.edit(embed=self.bot.util.embed(title="♠️ Multiplayer Blackjack ♥️", description="Starting in {}s\n{}/6 players".format((timer - c).seconds, len(self.blackjackgames[id]['players'])), footer="Use the blackjack command to join", color=self.color))
            self.blackjackgames[id]['state'] = "playing"
            if len(self.blackjackgames[id]['players']) > 6: self.blackjackgames[id]['players'] = self.blackjackgames[id]['players'][:6]
            await self.bot.util.clean(ctx, msg, 0, True)
            # game start
            # state: 0 = playing card down, 1 = playing card up, 2 = lost, 3 = won, 4 = blackjack
            status = [{'name':'Dealer', 'score':0, 'cards':[], 'state':0}]
            for p in self.blackjackgames[id]['players']:
                status.append({'name':ctx.guild.get_member(p).display_name, 'score':0, 'cards':[], 'state':0})
            final_msg = None
            deck = []
            kind = ["D", "S", "H", "C"]
            for i in range(51):
                deck.append('{}{}'.format((i % 13) + 1, kind[i // 13]))
            
            done = 0
            while done < len(status):
                msg = ""
                for p in range(len(status)):
                    if status[p]['state'] == 1:
                        c = deck[0]
                        deck = deck[1:]
                        value = int(c[:-1])
                        if value >= 10: value = 10
                        elif value == 1 and status[p]['score'] <= 10: value = 11
                        if status[p]['score'] + value > 21:
                            status[p]['state'] = 2
                            done += 1
                        elif status[p]['score'] + value == 21:
                            if len(status[p]['cards']) == 1: status[p]['state'] = 4
                            else: status[p]['state'] = 3
                            status[p]['score'] += value
                            done += 1
                        else:
                            status[p]['score'] += value
                        status[p]['cards'].append(c)
                    if p == 0: msg += ":spy: "
                    else: msg += "{} ".format(self.bot.emote.get(str(p)))
                    msg += self.pokerNameStrip(status[p]['name'])
                    msg += " \▫️ "
                    for i in range(len(status[p]['cards'])):
                        msg += "{}".format(status[p]['cards'][i].replace("D", "\♦️").replace("S", "\♠️").replace("H", "\♥️").replace("C", "\♣️").replace("11", "J").replace("12", "Q").replace("13", "K").replace("10", "tmp").replace("1", "A").replace("tmp", "10"))
                        if i == len(status[p]['cards']) - 1 and status[p]['state'] == 0: msg += ", 🎴"
                        elif i < len(status[p]['cards']) - 1: msg += ", "
                    if len(status[p]['cards']) == 0: msg += "🎴"
                    if status[p]['state'] == 0: status[p]['state'] = 1
                    elif status[p]['state'] == 1: status[p]['state'] = 0
                    msg += " \▫️ "
                    if status[p]['state'] == 4: msg += "**Blackjack**\n"
                    elif status[p]['state'] == 3: msg += "**21**\n"
                    elif status[p]['state'] == 2: msg += "Best {}\n".format(status[p]['score'])
                    else: msg += "{}\n".format(status[p]['score'])
                if final_msg is None: final_msg = await ctx.reply(embed=self.bot.util.embed(title="♠️ Multiplayer Blackjack ♥️", description=msg, color=self.color))
                else: await final_msg.edit(embed=self.bot.util.embed(title="♠️ Multiplayer Blackjack ♥️", description=msg, color=self.color))
                await asyncio.sleep(2)
            self.blackjackgames.pop(id)
            await self.bot.util.clean(ctx, final_msg, 45)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(10, 30, commands.BucketType.guild)
    async def dice(self, ctx, dice_string : str):
        """Roll some dies (format is NdN)
        Minimum is 1d6, Maximum is 10d100"""
        try:
            tmp = dice_string.lower().split('d')
            n = int(tmp[0])
            d = int(tmp[1])
            if n <= 0 or n> 10 or d < 6 or d > 100: raise Exception()
            final_msg = None
            rolls = []
            for i in range(n):
                rolls.append(random.randint(1, d))
                msg = ""
                for j in range(len(rolls)):
                    msg += "{}, ".format(rolls[j])
                    if j == (len(rolls) - 1): msg = msg[:-2]
                if len(rolls) == n:
                    msg += "\n**Total**: {:}, **Average**: {:}, **Percentile**: {:.1f}%".format(sum(rolls), round(sum(rolls)/len(rolls)), sum(rolls) * 100 / (n * d)).replace('.0%', '%')
                if final_msg is None: final_msg = await ctx.reply(embed=self.bot.util.embed(author={'name':"🎲 {} rolled {}...".format(ctx.author.display_name, dice_string), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color))
                else: await final_msg.edit(embed=self.bot.util.embed(author={'name':"🎲 {} rolled {}...".format(ctx.author.display_name, dice_string), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color))
                await asyncio.sleep(1)
        except:
            final_msg = await ctx.reply(embed=self.bot.util.embed(title="🎲 Dice Rolls", description="Invalid string `{}`\nFormat must be `NdN` (minimum is `1d6`, maximum is `10d100`)".format(dice_string), color=self.color))
        await self.bot.util.clean(ctx, final_msg, 80)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['flip'])
    @commands.cooldown(10, 30, commands.BucketType.guild)
    async def coin(self, ctx):
        """Flip a coin"""
        coin = random.randint(0, 1)
        final_msg = await ctx.reply(embed=self.bot.util.embed(author={'name':"{} flipped a coin...".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=(":coin: It landed on **Head**" if (coin == 0) else ":coin: It landed on **Tail**"), color=self.color))
        await self.bot.util.clean(ctx, final_msg, 60)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['chose', 'choice'])
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def choose(self, ctx, *, choices : str):
        """Select a random string from the user's choices
        Example: $choose I'm Alice ; Bob"""
        try:
            possible = choices.split(";")
            if len(possible) < 2: raise Exception()
            final_msg = await ctx.reply(embed=self.bot.util.embed(author={'name':"{}'s choice".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=random.choice(possible), color=self.color))
        except:
            final_msg = await ctx.reply(embed=self.bot.util.embed(title="Give me a list of something to choose from, separated by `;`", color=self.color))
        await self.bot.util.clean(ctx, final_msg, 45)

    @commands.command(no_pm=True, name="8ball", cooldown_after_parsing=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def _8ball(self, ctx, *, question : str):
        """Ask the magic ball a question"""
        final_msg = await ctx.reply(embed=self.bot.util.embed(author={'name':"{} asked".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description="`{}`\n{}".format(question, random.choice(["It is Certain.","It is decidedly so.","Without a doubt.","Yes definitely.","You may rely on it.","As I see it, yes.","Most likely.","Outlook good.","Yes.","Signs point to yes.","Reply hazy, try again.","Ask again later.","Better not tell you now.","Cannot predict now.","Concentrate and ask again.","Don't count on it.","My reply is no.","My sources say no.","Outlook not so good.","Very doubtful."])), color=self.color))
        await self.bot.util.clean(ctx, final_msg, 45)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def when(self, ctx, *, question : str = ""):
        """Ask the magic ball when will something happen"""
        final_msg = await ctx.reply(embed=self.bot.util.embed(author={'name':"{} asked".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description="`{}`\n{}".format(ctx.message.content[1:], random.choice(["Never", "Soon:tm:", "Ask again tomorrow", "Can't compute", "42", "One day, my friend", "Next year", "It's a secret to everybody", "Soon enough", "When it's ready", "Five minutes", "This week, surely", "My sources say next month", "NOW!", "I'm not so sure", "In three days"])), color=self.color))
        await self.bot.util.clean(ctx, final_msg, 45)