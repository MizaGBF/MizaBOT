from discord.ext import commands
import asyncio
import random
from collections import defaultdict

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

    def checkPokerHand(self, hand):
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
        elif flush and ((len(set(value_counts.values())) == 1 and (value_range==4)) or set(values) == set(["14", "2", "3", "4", "5"])): return "**Straight Flush, high {}**".format(self.highestCardStripped(list(value_counts.keys())).replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A"))
        elif sorted(value_counts.values()) == [1,4]: return "**Four of a Kind of {}**".format(list(value_counts.keys())[list(value_counts.values()).index(4)].replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A"))
        elif sorted(value_counts.values()) == [2,3]: return "**Full House, high {}**".format(list(value_counts.keys())[list(value_counts.values()).index(3)].replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A"))
        elif flush: return "**Flush**"
        elif (len(set(value_counts.values())) == 1 and (value_range==4)) or set(values) == set(["14", "2", "3", "4", "5"]): return "**Straight, high {}**".format(self.highestCardStripped(list(value_counts.keys())).replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A"))
        elif set(value_counts.values()) == set([3,1]): return "**Three of a Kind of {}**".format(list(value_counts.keys())[list(value_counts.values()).index(3)].replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A"))
        elif sorted(value_counts.values())==[1,2,2]:
            k = list(value_counts.keys())
            k.pop(list(value_counts.values()).index(1))
            return "**Two Pairs, high {}**".format(self.highestCardStripped(k).replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A"))
        elif 2 in value_counts.values(): return "**Pair of {}**".format(list(value_counts.keys())[list(value_counts.values()).index(2)].replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A"))
        else: return "**Highest card is {}**".format(self.highestCard(hand).replace("D", "\♦️").replace("S", "\♠️").replace("H", "\♥️").replace("C", "\♣️").replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A"))

    def highestCardStripped(self, selection):
        ic = [int(i) for i in selection]
        return str(sorted(ic)[-1])

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
                else: msg += hand[i].replace("D", "\♦️").replace("S", "\♠️").replace("H", "\♥️").replace("C", "\♣️").replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A")
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
            cd = 29
            while cd >= 0:
                await asyncio.sleep(1)
                await msg.edit(embed=self.bot.util.embed(title="♠️ Multiplayer Poker ♥️", description="Starting in {}s\n{}/6 players".format(cd, len(self.pokergames[id]['players'])), footer="Use the poker command to join", color=self.color))
                cd -= 1
                if len(self.pokergames[id]['players']) >= 6:
                    break
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
                    else: msg += draws[j].replace("D", "\♦️").replace("S", "\♠️").replace("H", "\♥️").replace("C", "\♣️").replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A")
                    if j < 2: msg += ", "
                    else: msg += "\n\n"
                n = max(1, s)
                for x in range(0, len(self.pokergames[id]['players'])):
                    pid = self.pokergames[id]['players'][x]
                    msg += "{} {} \▫️ ".format(self.bot.emote.get(str(x+1)), self.pokerNameStrip(ctx.guild.get_member(pid).display_name))
                    if s == 4:
                        highest = self.highestCard(draws[3+2*x:5+2*x])
                    for j in range(0, 2):
                        if j > s: msg += "🎴"
                        elif s == 4 and draws[3+j+2*x] == highest: msg += "__" + draws[3+j+2*x].replace("D", "\♦️").replace("S", "\♠️").replace("H", "\♥️").replace("C", "\♣️").replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A") + "__"
                        else: msg += draws[3+j+2*x].replace("D", "\♦️").replace("S", "\♠️").replace("H", "\♥️").replace("C", "\♣️").replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A")
                        if j == 0: msg += ", "
                        else:
                            if s == 4:
                                msg += " \▫️ "
                                hand = draws[0:3] + draws[3+2*x:5+2*x]
                                hstr = await self.bot.do(self.checkPokerHand, hand)
                                if hstr.startswith("**Highest"):
                                    msg += "**Highest card is {}**".format(self.highestCard(draws[3+2*x:5+2*x]).replace("D", "\♦️").replace("S", "\♠️").replace("H", "\♥️").replace("C", "\♣️").replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A"))
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
            cd = 29
            while cd >= 0:
                await asyncio.sleep(1)
                await msg.edit(embed=self.bot.util.embed(title="♠️ Multiplayer Blackjack ♥️", description="Starting in {}s\n{}/6 players".format(cd, len(self.blackjackgames[id]['players'])), footer="Use the blackjack command to join", color=self.color))
                cd -= 1
                if len(self.blackjackgames[id]['players']) >= 6:
                    break
            self.blackjackgames[id]['state'] = "playing"
            if len(self.blackjackgames[id]['players']) > 6: self.blackjackgames[id]['players'] = self.blackjackgames[id]['players'][:6]
            await self.bot.util.clean(ctx, msg, 0, True)
            # game start
            status = []
            for p in self.blackjackgames[id]['players']:
                status.append({'name':ctx.guild.get_member(p).display_name, 'score':0, 'cards':[], 'state':0})
            status.append({'name':'Dealer', 'score':0, 'cards':[], 'state':0}) # 0 = playing card down, 1 = playing card up, 2 = lost, 3 = won, 4 = blackjack
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
                    if p == len(status) - 1: msg += "\n:spy: "
                    else: msg += "{} ".format(self.bot.emote.get(str(p+1)))
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