from . import BaseView
import disnake
import random
import asyncio
from datetime import timedelta

# ----------------------------------------------------------------------------------------------------------------
# Poker View
# ----------------------------------------------------------------------------------------------------------------
# View class used to play Poker
# PokerSub is for ephemeral messages
# ----------------------------------------------------------------------------------------------------------------

class PokerSub(BaseView):
    """__init__()
    Constructor
    
    Parameters
    ----------
    bot: a pointer to the bot for ease of access
    parent: the Poker view
    """
    def __init__(self, bot, parent):
        super().__init__(bot, timeout=480)
        self.parent = parent

    """do()
    Coroutine called by buttons
    
    Parameters
    ----------
    interaction: the button interaction
    mode: 0 = confirm, 1 = toggle card 1, 2 = toggle card 2
    """
    async def do(self, interaction: disnake.Interaction, mode : int):
        for i, p in enumerate(self.parent.players):
            if p.id == interaction.user.id:
                break
        if self.parent.hands[i][0] >= 100:
            await interaction.response.send_message("You can't modify your choice", ephemeral=True)
            return
        match mode:
            case 0:
                if self.parent.hands[i][0] < 10: self.parent.hands[i][1][0] = self.parent.deck.pop()
                if self.parent.hands[i][0] in [0, 10]: self.parent.hands[i][1][1] = self.parent.deck.pop()
                self.parent.hands[i][0] += 100
                self.parent.updateSubEmbed(i)
                await interaction.response.edit_message(embed=self.parent.subembeds[i], view=None)
                for h in self.parent.hands:
                    if h[0] < 100: return
                self.stopall()
                self.parent.stopall()
                self.parent.state = 1
            case 1:
                if self.parent.hands[i][0] in [10, 11]: self.parent.hands[i][0] -= 10
                else: self.parent.hands[i][0] += 10
                self.parent.updateSubEmbed(i)
                await interaction.response.edit_message(embed=self.parent.subembeds[i], view=self)
            case 2:
                if self.parent.hands[i][0] in [1, 11]: self.parent.hands[i][0] -= 1
                else: self.parent.hands[i][0] += 1
                self.parent.updateSubEmbed(i)
                await interaction.response.edit_message(embed=self.parent.subembeds[i], view=self)

    @disnake.ui.button(label='Toggle Card 1', style=disnake.ButtonStyle.success)
    async def holdcard1(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        if self.parent.state == 0:
            await self.do(interaction, 1)
        else:
            await interaction.response.send_message("The game is over", ephemeral=True)

    @disnake.ui.button(label='Toggle Card 2', style=disnake.ButtonStyle.success)
    async def holdcard2(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        if self.parent.state == 0:
            await self.do(interaction, 2)
        else:
            await interaction.response.send_message("The game is over", ephemeral=True)

    @disnake.ui.button(label='Confirm', style=disnake.ButtonStyle.danger)
    async def confirm(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        if self.parent.state == 0:
            await self.do(interaction, 0)
        else:
            await interaction.response.send_message("The game is over", ephemeral=True)

class Poker(BaseView):
    """__init__()
    Constructor
    
    Parameters
    ----------
    bot: a pointer to the bot for ease of access
    players: list of Players
    embed: disnake.Embed to edit
    """
    def __init__(self, bot, players : list, embed : disnake.Embed):
        super().__init__(bot, timeout=180)
        self.state = 0
        self.players = players
        random.shuffle(self.players)
        self.embed = embed
        self.deck = []
        kind = ["D", "S", "H", "C"]
        for i in range(51):
            self.deck.append('{}{}'.format((i % 13) + 2, kind[i // 13]))
        random.shuffle(self.deck)
        self.dealer = [self.deck.pop(), self.deck.pop(), self.deck.pop()]
        self.hands = []
        for i in range(len(self.players)):
            self.hands.append([11, [self.deck.pop(), self.deck.pop()]])
        self.sub = PokerSub(self.bot, self)
        self.subembeds = []
        for i, p in enumerate(self.players):
            self.subembeds.append(self.bot.util.embed(title="♠️ {}'s hand ♥".format(p.display_name), description="Initialization", color=self.embed.color))
            self.updateSubEmbed(i)

    """update()
    Update the embed
    
    Parameters
    ----------
    inter: an interaction
    init: if True, it uses a different method (only used from the command call itself)
    """
    async def update(self, inter, init=False):
        self.embed.description = ":spy: Dealer ▫️ "
        match self.state:
            case 0: self.embed.description += "🎴, 🎴, 🎴\n"
            case 1: self.embed.description += "🎴, 🎴, 🎴\n"
            case 2: self.embed.description += "{}, 🎴, 🎴\n".format(Poker.valueNsuit2head(self.dealer[0]))
            case 3: self.embed.description += "{}, {}, 🎴\n".format(Poker.valueNsuit2head(self.dealer[0]), Poker.valueNsuit2head(self.dealer[1]))
            case _: self.embed.description += "{}, {}, {}\n".format(Poker.valueNsuit2head(self.dealer[0]), Poker.valueNsuit2head(self.dealer[1]), Poker.valueNsuit2head(self.dealer[2]))
        if self.state == 0:
            for i, p in enumerate(self.players):
                self.embed.description += "{} {} \▫️ 🎴, 🎴\n".format(self.bot.emote.get(str(i+1)), (p.display_name if len(p.display_name) <= 10 else p.display_name[:10] + "..."))
            self.embed.description += "Waiting for all players to make their choices"
        elif self.state <= 4:
            for i, p in enumerate(self.players):
                self.embed.description += "{} {} \▫️ 🎴, 🎴\n".format(self.bot.emote.get(str(i+1)), (p.display_name if len(p.display_name) <= 10 else p.display_name[:10] + "..."))
        elif self.state == 5:
            for i, p in enumerate(self.players):
                self.embed.description += "{} {} \▫️ {}, 🎴\n".format(self.bot.emote.get(str(i+1)), (p.display_name if len(p.display_name) <= 10 else p.display_name[:10] + "..."), Poker.valueNsuit2head(self.hands[i][1][0]))
        else:
            winner = []
            best = 0
            for i, p in enumerate(self.players):
                hs, hstr = Poker.checkPokerHand(self.dealer + self.hands[i][1])
                if hs == best: winner.append(p)
                elif hs > best:
                    best = hs
                    winner = [p]
                self.embed.description += "{} {} \▫️ {}, {}, {}\n".format(self.bot.emote.get(str(i+1)), (p.display_name if len(p.display_name) <= 10 else p.display_name[:10] + "..."), Poker.valueNsuit2head(self.hands[i][1][0]), Poker.valueNsuit2head(self.hands[i][1][1]), hstr)
            match len(winner):
                case 0: pass # shouldn't happen
                case 1:
                    self.embed.description += "**{}** is the winner".format(winner[0].display_name)
                case _:
                    self.embed.description += "It's a **draw** between "
                    for p in winner:
                        self.embed.description += "{}, ".format(p.display_name)
                    self.embed.description = self.embed.description[:-2]
        if init:
            await inter.edit_original_message(embed=self.embed, view=self)
            self.message = await inter.original_message()
        elif self.state >= 0: await self.message.edit(embed=self.embed, view=None)
        else: await self.message.edit(embed=self.embed, view=view)

    """giveup()
    The stop button coroutine callback.
    Allow the player to stop.
    
    Parameters
    ----------
    button: the Discord button
    button: a Discord interaction
    """
    @disnake.ui.button(label='See Your Hand', style=disnake.ButtonStyle.primary)
    async def control(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        i = None
        for idx, p in enumerate(self.players):
            if p.id == interaction.user.id:
                i = idx
                break
        if self.state == 0 and i is not None:
            await interaction.response.send_message(embed=self.subembeds[i], view=self.sub, ephemeral=True)
        else:
            await interaction.response.send_message("You can't play this game", ephemeral=True)

    """updateSubEmbed()
    Update an user embed
    
    Parameters
    ----------
    index: Player index
    """
    def updateSubEmbed(self, index):
        self.subembeds[index].description = "{} {} ▫️ {} {}\n".format(Poker.valueNsuit2head(self.hands[index][1][0]), ("**Holding**" if self.hands[index][0] in [10, 11] else ""), Poker.valueNsuit2head(self.hands[index][1][1]), ("**Holding**" if self.hands[index][0] in [1, 11] else ""))
        if self.hands[index][0] >= 100:
            self.subembeds[index].description += "**Your hand is locked**\nPlease wait for other players to confirm\n"

    """final()
    Coroutine to announce the results
    """
    async def final(self):
        while self.state < 7:
            await asyncio.sleep(1)
            await self.update(None)
            self.state += 1

    """value2head()
    Convert a card value to a string.
    Heads are converted to the equivalent (J, Q, K, A)
    
    Parameters
    ----------
    value: Integer or string card value
    
    Returns
    --------
    str: Card string
    """
    def value2head(value):
        return str(value).replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A")

    """valueNsuit2head()
    Convert a card value and suit to a string.
    Heads are converted to the equivalent (J, Q, K, A).
    Suits are converted to ♦, ♠️, ♥️ and ♣️
    
    Parameters
    ----------
    value: String card value
    
    Returns
    --------
    str: Card string
    """
    def valueNsuit2head(value):
        return value.replace("D", "\♦️").replace("S", "\♠️").replace("H", "\♥️").replace("C", "\♣️").replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A")

    """checkPokerHand()
    Check a poker hand strength
    
    Parameters
    ----------
    hand: List of card to check
    
    Returns
    --------
    tuple:
        - int : Strength value
        - str: Strength string
    """
    def checkPokerHand(hand):
        flush = False
        # flush detection
        suits = [h[-1] for h in hand]
        if len(set(suits)) == 1: flush = True
        # other checks
        values = [i[:-1] for i in hand] # get card values
        value_counts = {}
        for v in values:
            value_counts[v] = value_counts.get(v, 0) + 1 # count each match
        rank_values = [int(i) for i in values] # rank them
        value_range = max(rank_values) - min(rank_values) # and get the difference
        # determinate hand from their
        # checks happen in strength order
        if flush and set(values) == set(["10", "11", "12", "13", "14"]):
            return 800 + int(Poker.highestCard(hand)[:-1]), "**Royal Straight Flush**"
        elif flush and ((len(set(value_counts.values())) == 1 and (value_range==4)) or set(values) == set(["14", "2", "3", "4", "5"])):
            return "**Straight Flush, high {}**".format(Poker.value2head(Poker.highestCardStripped(list(value_counts.keys()))))
        elif sorted(value_counts.values()) == [1,4]:
            return 700 + int(list(value_counts.keys())[list(value_counts.values()).index(4)]), "**Four of a Kind of {}**".format(Poker.value2head(list(value_counts.keys())[list(value_counts.values()).index(4)]))
        elif sorted(value_counts.values()) == [2,3]:
            return 600 + int(list(value_counts.keys())[list(value_counts.values()).index(3)]), "**Full House, high {}**".format(Poker.value2head(list(value_counts.keys())[list(value_counts.values()).index(3)]))
        elif flush:
            return 500 + int(Poker.highestCard(hand)[:-1]), "**Flush**"
        elif (len(set(value_counts.values())) == 1 and (value_range==4)) or set(values) == set(["14", "2", "3", "4", "5"]):
            return 400 + int(Poker.highestCardStripped(list(value_counts.keys()))), "**Straight, high {}**".format(Poker.value2head(Poker.highestCardStripped(list(value_counts.keys()))))
        elif set(value_counts.values()) == set([3,1]):
            return 300 + int(list(value_counts.keys())[list(value_counts.values()).index(3)]), "**Three of a Kind of {}**".format(Poker.value2head(list(value_counts.keys())[list(value_counts.values()).index(3)]))
        elif sorted(value_counts.values())==[1,2,2]:
            k = list(value_counts.keys())
            k.pop(list(value_counts.values()).index(1))
            return 200 + int(Poker.highestCardStripped(k)), "**Two Pairs, high {}**".format(Poker.value2head(Poker.highestCardStripped(k)))
        elif 2 in value_counts.values():
            return 100 + int(list(value_counts.keys())[list(value_counts.values()).index(2)]), "**Pair of {}**".format(Poker.value2head(list(value_counts.keys())[list(value_counts.values()).index(2)]))
        else:
            return int(Poker.highestCard(hand)[:-1]), "**Highest card is {}**".format(Poker.value2head(Poker.highestCard(hand).replace("D", "\♦️").replace("S", "\♠️").replace("H", "\♥️").replace("C", "\♣️")))

    """highestCardStripped()
    Return the highest card in the selection, without the suit
    
    Parameters
    ----------
    selection: List of card to check
    
    Returns
    --------
    str: Highest card
    """
    def highestCardStripped(selection):
        ic = [int(i) for i in selection] # convert to int
        return str(sorted(ic)[-1]) # sort and then convert back to str

    """highestCard()
    Return the highest card in the selection
    
    Parameters
    ----------
    selection: List of card to check
    
    Returns
    --------
    str: Highest card
    """
    def highestCard(selection):
        for i, c in enumerate(selection):
            selection[i] = c.zfill(3)
        last = sorted(selection)[-1]
        if last[0] == '0': last = last[1:]
        return last