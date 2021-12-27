from . import BaseView
import disnake
import random

# ----------------------------------------------------------------------------------------------------------------
# Blackjack View
# ----------------------------------------------------------------------------------------------------------------
# View class used for the blackjack minigame
# ----------------------------------------------------------------------------------------------------------------

class Blackjack(BaseView):
    """__init__()
    Constructor
    
    Parameters
    ----------
    bot: a pointer to the bot for ease of access
    players: list of Players
    embed: disnake.Embed to edit
    """
    def __init__(self, bot, players : list, embed : disnake.Embed):
        super().__init__(bot, timeout=240)
        self.state = 0
        self.players = players
        if len(self.players) < 6: self.players.append(self.bot.user)
        random.shuffle(self.players)
        self.embed = embed
        self.deck = []
        kind = ["D", "S", "H", "C"]
        for i in range(51):
            self.deck.append('{}{}'.format((i % 13) + 1, kind[i // 13]))
        random.shuffle(self.deck)
        self.hands = []
        for i in range(len(self.players)):
            self.hands.append([0, [self.deck.pop()]]) # playing state, cards
        if self.players[self.state].id == self.bot.user.id:
            self.playai()
        self.notification = "Turn of **{}**".format(self.players[self.state].display_name)

    """formatHand()
    Generate a Hand string for the given hand
    
    Parameters
    ----------
    hand: one item from self.hands
    playing: boolean, True if it's the currently playing user
    
    Returns
    ----------
    str: resulting string
    """
    def formatHand(self, hand, playing):
        msg = ""
        score = 0
        for card in hand[1]:
            msg += "{}, ".format(card.replace("D", "\♦️").replace("S", "\♠️").replace("H", "\♥️").replace("C", "\♣️").replace("11", "J").replace("12", "Q").replace("13", "K").replace("10", "tmp").replace("1", "A").replace("tmp", "10"))
            if card[:-1] == "1" and score < 11: score += 11
            elif int(card[:-1]) >= 10: score += 10
            else: score += int(card[:-1])
        msg = msg[:-2]
        if playing:
            msg += ", 🎴"
        msg += " \▫️"
        match hand[0]:
            case 0: msg += " Score is **{}**".format(score)
            case 1: msg += " Stopped at **{}**".format(score)
            case 2: msg += " **Blackjack**"
            case 3: msg += " Reached **21**"
            case 4: msg += " **Lost**"
        return msg

    """getWinner()
    Generate a string indicating who won the game

    Returns
    ----------
    str: resulting string
    """
    def getWinner(self):
        winner = []
        best = 0
        for i, p in enumerate(self.players):
            if self.hands[i][0] == 4:
                continue
            else:
                score = 0
                for card in self.hands[i][1]:
                    if card[:-1] == "1" and score < 11: score += 11
                    elif int(card[:-1]) >= 10: score += 10
                    else: score += int(card[:-1])
                if score == 21 and len(self.hands[i][1]) == 2: score = 22
                if score == best:
                    winner.append(p)
                elif score > best:
                    winner = [p]
                    best = score
        match len(winner):
            case 0:
                return "No one won"
            case 1:
                return "**{}** is the winner".format(winner[0].display_name)
            case _:
                msg = "It's a **draw** between "
                for p in winner:
                    msg += "{}, ".format(p.display_name)
                return msg[:-2]

    """update()
    Update the embed
    
    Parameters
    ----------
    inter: an interaction
    init: if True, it uses a different method (only used from the command call itself)
    """
    async def update(self, inter, init=False):
        self.embed.description = ""
        for i, p in enumerate(self.players):
            self.embed.description += "{} {} \▫️ {}\n".format(self.bot.emote.get(str(i+1)), (p.display_name if len(p.display_name) <= 10 else p.display_name[:10] + "..."), self.formatHand(self.hands[i], (i == self.state)))
        self.embed.description += self.notification
        if init: await inter.edit_original_message(embed=self.embed, view=self)
        elif self.state >= 0: await inter.response.edit_message(embed=self.embed, view=self)
        else: await inter.response.edit_message(embed=self.embed, view=None)

    """playai()
    The AI for MizaBOT
    """
    def playai(self):
        score = 0
        for card in self.hands[self.state][1]:
            if card[:-1] == "1" and score < 11: score += 11
            elif int(card[:-1]) >= 10: score += 10
            else: score += int(card[:-1])
        if score < 12:
            self.play(False)
        else:
            if score >= 19:
                self.play(True)
            if score >= 17:
                self.play(random.randint(1, 100) < 10)
            elif score >= 15:
                self.play(random.randint(1, 100) < 40)
            else:
                self.play(random.randint(1, 100) < 80)

    """play()
    Allow the player to make a move
    
    Parameters
    ----------
    stop: boolean, True for the player to stop, False to draw a card
    """
    def play(self, stop):
        if stop:
            self.hands[self.state][0] = 1
        else:
            self.hands[self.state][1].append(self.deck.pop())
            score = 0
            for card in self.hands[self.state][1]:
                if card[:-1] == "1" and score < 11: score += 11
                elif int(card[:-1]) >= 10: score += 10
                else: score += int(card[:-1])
            if score == 21:
                if len(self.hands[self.state][1]) == 2: self.hands[self.state][0] = 2
                else: self.hands[self.state][0] = 3
            elif score > 21: self.hands[self.state][0] = 4
        current_state = self.state
        while True:
            self.state = (self.state + 1) % len(self.players)
            if self.hands[self.state][0] == 0:
                break
            elif current_state == self.state:
                self.state = -1
                break
        if self.players[self.state].id == self.bot.user.id and self.hands[self.state][0] == 0:
            self.playai()

    """draw()
    The draw button coroutine callback.
    Allow the player to draw a card.
    
    Parameters
    ----------
    button: the Discord button
    button: a Discord interaction
    """
    @disnake.ui.button(label='Draw Card', style=disnake.ButtonStyle.success)
    async def draw(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        if self.state >= 0 and self.players[self.state].id == interaction.user.id:
            self.play(False)
            if self.state >= 0:
                self.notification = "Turn of **{}**".format(self.players[self.state].display_name)
            else:
                self.notification = self.getWinner()
                self.stopall()
            await self.update(interaction)
        else:
            await interaction.response.send_message("It's not your turn to play or you aren't the player", ephemeral=True)

    """giveup()
    The stop button coroutine callback.
    Allow the player to stop.
    
    Parameters
    ----------
    button: the Discord button
    button: a Discord interaction
    """
    @disnake.ui.button(label='Stop', style=disnake.ButtonStyle.danger)
    async def giveup(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        if self.state >= 0 and self.players[self.state].id == interaction.user.id:
            self.play(True)
            if self.state >= 0:
                self.notification = "Turn of **{}**".format(self.players[self.state].display_name)
            else:
                self.notification = "The game ended"
                self.stopall()
            await self.update(interaction)
        else:
            await interaction.response.send_message("It's not your turn to play or you aren't the player", ephemeral=True)