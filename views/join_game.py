from . import BaseView
import disnake
import asyncio
from datetime import datetime, timedelta

# ----------------------------------------------------------------------------------------------------------------
# JoinGame View
# ----------------------------------------------------------------------------------------------------------------
# View class used to join games
# ----------------------------------------------------------------------------------------------------------------

class JoinGame(BaseView):
    """__init__()
    Constructor
    
    Parameters
    ----------
    bot: a pointer to the bot for ease of access
    players: list of disnake.User/Member participating
    limit: player count limit
    """
    def __init__(self, bot, players : list, limit : int):
        super().__init__(bot)
        self.players = players
        self.limit = limit

    """updateTimer()
    Coroutine to update the waiting message
    
    Parameters
    ----------
    msg: disnake.Message to update
    embed: embed to update and put in msg
    desc: description of the embed to update, must contains two {} for the formatting
    limit: time limit in 30s
    """
    async def updateTimer(self, msg, embed, desc, limit):
        timer = self.bot.util.JST() + timedelta(seconds=limit)
        while True:
            await asyncio.sleep(1)
            c = self.bot.util.JST()
            if c >= timer or len(self.players) >= self.limit:
                break
            embed.description = desc.format((timer - c).seconds, len(self.players))
            await msg.edit(embed=embed)
        self.stopall()
        button.disabled = True

    """isParticipating()
    Check if the given id is from a participating user
    
    Parameters
    ----------
    id: disnake.User/Member id
    
    Returns
    ----------
    bool: True if participating, False if not
    """
    def isParticipating(self, id):
        for p in self.players:
            if p.id == id:
                return True
        return False

    """joinbutton()
    The Join button coroutine callback.
    
    Parameters
    ----------
    button: the disnake button
    button: a disnake interaction
    """
    @disnake.ui.button(label='Join', style=disnake.ButtonStyle.blurple)
    async def joinbutton(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        self.update_last(interaction)
        if not button.disabled and not self.isParticipating(interaction.user.id):
            self.players.append(interaction.user)
            await interaction.response.send_message("You are registered", ephemeral=True)
            if len(self.players) >= self.limit:
                self.stopall()
                button.disabled = True
        else:
            await interaction.response.send_message("You are already participating OR the game started", ephemeral=True)