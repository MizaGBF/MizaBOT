from . import BaseView
import disnake

# ----------------------------------------------------------------------------------------------------------------
# Page View
# ----------------------------------------------------------------------------------------------------------------
# View class used to add Previous and Next buttons to cycle between multiple embeds
# ----------------------------------------------------------------------------------------------------------------

class Page(BaseView):
    """__init__()
    Constructor
    
    Parameters
    ----------
    bot: a pointer to the bot for ease of access
    owner_id: the id of the user responsible for the interaction, leave to None to ignore
    timeout: timeout in second before the interaction becomes invalid
    """
    def __init__(self, bot, owner_id : int, embeds : list, timeout : float = 120.0):
        super().__init__(bot, owner_id=owner_id, timeout=timeout, enable_timeout_cleanup=False)
        self.current = 0
        self.embeds = embeds

    """prev()
    The previous button coroutine callback.
    Change the self.message to the previous embed
    
    Parameters
    ----------
    button: the Discord button
    button: a Discord interaction
    """
    @disnake.ui.button(label='Previous', style=disnake.ButtonStyle.blurple)
    async def prev(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        if not button.disabled and self.ownership_check(interaction):
            if len(self.embeds) > 0:
                self.current = (self.current + len(self.embeds) - 1) % len(self.embeds)
                await interaction.send("Page successful changed to {}".format(self.current+1), ephemeral=True)
                await self.message.edit(embed=self.embeds[self.current])
            else:
                await interaction.send("Impossible to change pages", ephemeral=True)
        else:
            await interaction.response.send_message("You can't press this button", ephemeral=True)

    """next()
    The next button coroutine callback.
    Change the self.message to the next embed
    
    Parameters
    ----------
    button: the Discord button
    button: a Discord interaction
    """
    @disnake.ui.button(label='Next', style=disnake.ButtonStyle.blurple)
    async def next(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        if not button.disabled and self.ownership_check(interaction):
            if len(self.embeds) > 0:
                self.current = (self.current + 1) % len(self.embeds)
                await interaction.send("Page successful changed to {}".format(self.current+1), ephemeral=True)
                await self.message.edit(embed=self.embeds[self.current])
            else:
                await interaction.send("Impossible to change pages", ephemeral=True)
        else:
            await interaction.response.send_message("You can't press this button", ephemeral=True)