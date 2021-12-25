from . import BaseView
import disnake
import random

# ----------------------------------------------------------------------------------------------------------------
# Chest Rush View
# ----------------------------------------------------------------------------------------------------------------
# Chest Rush class and its button used by the chest rush game
# ----------------------------------------------------------------------------------------------------------------

class ChestRushButton(disnake.ui.Button):
    """__init__()
    Button Constructor
    
    Parameters
    ----------
    grid: the list of remaining winnable items
    row: an integer indicating on what row to set the button on
    """
    def __init__(self, grid : str, row : int):
        super().__init__(style=disnake.ButtonStyle.secondary, label='Chest', row=row)
        self.grid = grid

    """callback()
    Coroutine callback called when the button is called
    Stop the view when the game is won
    
    Parameters
    ----------
    interaction: a Discord interaction
    """
    async def callback(self, interaction: disnake.Interaction):
        if not self.disabled and self.view.ownership_check(interaction):
            self.disabled = True
            self.label = self.view.grid.pop()
            if self.label.startswith('$$$'):
                self.style = disnake.ButtonStyle.success
                self.label = self.label[3:]
            else:
                self.style = disnake.ButtonStyle.primary
            if self.view.check_status():
                self.view.stopall()
                msg = await interaction.response.edit_message(embed=self.view.bot.util.embed(author={'name':"{} opened".format(interaction.user.display_name), 'icon_url':interaction.user.display_avatar}, color=self.view.color), view=self.view)
                await self.view.bot.util.clean(interaction, 70)
            else:
                await interaction.response.edit_message(view=self.view)
        else:
            await interaction.response.send_message("You can't press this button", ephemeral=True)

class ChestRush(BaseView):
    """__init__()
    Constructor
    
    Parameters
    ----------
    bot: a pointer to the bot for ease of access
    owner_id: the id of the user responsible for the interaction, leave to None to ignore
    grid: list of items to be hidden behind the buttons
    color: the color to be used for the message embed
    """
    def __init__(self, bot, owner_id : int, grid, color : int):
        super().__init__(bot, owner_id=owner_id, timeout=120.0)
        self.grid = grid
        self.color = color
        for i in range(9):
            self.add_item(ChestRushButton(self.grid, i // 3))

    """check_status()
    Function to check the game state
    
    Parameters
    ----------
    item: the last item revealed behind a button
    
    Returns
    --------
    bool: True if the game is over, False if not
    """
    def check_status(self):
        if len(self.grid) == 0:
            for c in self.children:
                if not c.disabled:
                    c.disabled = True
                    c.label = '\u200b'
            return True
        elif len(self.grid) == 1 and self.grid[0].startswith("###"):
            self.grid[0] = self.grid[0].replace("###", "$$$")
            while True:
                c = random.choice(self.children)
                if c.disabled: continue
                c.style = disnake.ButtonStyle.danger
                c.label = "Surprise"
                for c in self.children:
                    if not c.disabled and c.style != disnake.ButtonStyle.danger:
                        c.disabled = True
                        c.label = '\u200b'
                break
        return False