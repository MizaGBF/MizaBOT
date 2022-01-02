from . import BaseView
import disnake
import random
import asyncio

# ----------------------------------------------------------------------------------------------------------------
# RPS View
# ----------------------------------------------------------------------------------------------------------------
# View class used to play Rock Paper Scissor
# ----------------------------------------------------------------------------------------------------------------

class RPS(BaseView):
    """__init__()
    Constructor
    
    Parameters
    ----------
    bot: a pointer to the bot for ease of access
    players: list of Players
    embed: disnake.Embed to edit
    scores: list, current player scores
    target: number of round won to win
    """
    def __init__(self, bot, players : list, embed : disnake.Embed, scores : list, target : int):
        super().__init__(bot, timeout=60)
        self.players = players
        self.embed = embed
        self.scores = scores
        self.target = target
        self.state = [-1, -1]
        self.won = False

    """update()
    Update the embed
    
    Parameters
    ----------
    inter: an interaction
    init: if True, it uses a different method (only used from the command call itself)
    """
    async def update(self, inter, init=False):
        if not self.won:
            if self.state[0] == -1 or self.state[1] == -1:
                self.embed.description = ""
                for i, p in enumerate(self.players):
                    self.embed.description += "**{}** ▫️ ".format(p.display_name)
                    if self.state[i] == -1: self.embed.description += "*is thinking...*\n"
                    else: self.embed.description += "*made its choice.*\n"
            else:
                self.embed.description = ""
                for i, p in enumerate(self.players):
                    self.embed.description += "**{}** ▫️ ".format(p.display_name)
                    match self.state[i]:
                        case 0: self.embed.description += "selected 🪨 **Rock**\n"
                        case 1: self.embed.description += "selected 🧻 **Paper**\n"
                        case 2: self.embed.description += "selected ✂️ **Scissor**\n"
                # winner selection
                if self.state[0] == self.state[1]:
                    self.embed.description += "This round is a **draw**\n"
                    self.embed.description += "**Next round in 10 seconds...**"
                    self.won = True
                else:
                    v = self.state[0] * 10 + self.state[1]
                    win = None
                    match v:
                        case  1: win = 1
                        case  2: win = 0
                        case 10: win = 0
                        case 12: win = 1
                        case 20: win = 1
                        case 21: win = 0
                    self.scores[win] += 1
                    self.won = True
                    if self.target > 1:
                        self.embed.description += "**{}** won this round\n".format(self.players[win].display_name)
                        self.embed.description += "**{}** won {} time(s) ▫️ **{}** won {} time(s)\n".format(self.players[0].display_name, self.scores[0], self.players[1].display_name, self.scores[1])
                        if self.scores[win] >= self.target:
                            self.embed.description += "**{}** is the **Winner**".format(self.players[win].display_name)
                        else:
                            self.embed.description += "**Next round in 10 seconds...**"
                    else:
                        self.embed.description += "**{}** is the **Winner**".format(self.players[win].display_name)
                self.stopall()
        if init:
            await inter.edit_original_message(content=self.bot.util.players2mentions(self.players), embed=self.embed, view=self)
            self.message = await inter.original_message()
        elif not self.won: await self.message.edit(embed=self.embed, view=self)
        else: await self.message.edit(embed=self.embed, view=None)

    """timeoutCheck()
    Force a result if the view timedout
    
    Parameters
    ----------
    inter: a Discord interaction
    """
    async def timeoutCheck(self, inter):
        if not self.won:
            if self.state[0] == -1: self.state[0] = random.randint(0, 2)
            if self.state[1] == -1: self.state[1] = random.randint(0, 2)
            await self.update(inter)

    """callback()
    Callback for the various buttons
    
    Parameters
    ----------
    interaction: a Discord interaction
    action: integer, what item the player picked
    """
    async def callback(self, interaction: disnake.Interaction, action: int):
        await interaction.response.defer(ephemeral=True)
        i = None
        for idx, p in enumerate(self.players):
            if p.id == interaction.user.id:
                if self.state[idx] == -1:
                    i = idx
                    break
        if i is not None:
            if self.state[i] != -1:
                await interaction.edit_original_message("You can't change your choice")
            else:
                self.state[i] = action
                await self.update(interaction)
                match action:
                    case 0:
                        await interaction.edit_original_message("You selected Rock")
                    case 1:
                        await interaction.edit_original_message("You selected Paper")
                    case 2:
                        await interaction.edit_original_message("You selected Scissor")
        else:
            await interaction.edit_original_message("You can't play this game")

    @disnake.ui.button(label='Rock', style=disnake.ButtonStyle.primary, emoji='🪨')
    async def rock(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        await self.callback(interaction, 0)

    @disnake.ui.button(label='Paper', style=disnake.ButtonStyle.primary, emoji='🧻')
    async def paper(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        await self.callback(interaction, 1)

    @disnake.ui.button(label='Scissor', style=disnake.ButtonStyle.primary, emoji='✂️')
    async def scissor(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        await self.callback(interaction, 2)