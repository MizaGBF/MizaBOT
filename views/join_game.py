from . import BaseView
import disnake
import asyncio
from datetime import timedelta

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
    callback: coroutine to be called on button press (optional)
    """
    def __init__(self, bot, players : list, limit : int, callback = None):
        super().__init__(bot)
        self.players = players
        self.limit = limit
        self.callback = (self.default_callback if callback is None else callback)

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

    """default_callback()
    Default and example of a callback to use on button press
    
    Parameters
    ----------
    interaction: a disnake interaction
    """
    async def default_callback(self, interaction):
        await interaction.response.send_message("You are registered", ephemeral=True)

    """joinbutton()
    The Join button coroutine callback.
    
    Parameters
    ----------
    button: the disnake button
    interaction: a disnake interaction
    """
    @disnake.ui.button(label='Join', style=disnake.ButtonStyle.blurple)
    async def joinbutton(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        if not button.disabled and not self.isParticipating(interaction.user.id):
            self.players.append(interaction.user)
            await self.callback(interaction)
            if len(self.players) >= self.limit:
                self.stopall()
                button.disabled = True
        else:
            await interaction.response.send_message("You are already participating OR the game started", ephemeral=True)