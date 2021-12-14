from . import BaseView
import disnake

# ----------------------------------------------------------------------------------------------------------------
# Scratcher View
# ----------------------------------------------------------------------------------------------------------------
# Scratcher class and its button used by the scratcher game
# ----------------------------------------------------------------------------------------------------------------

class ScratcherButton(disnake.ui.Button):
    """__init__()
    Button Constructor
    
    Parameters
    ----------
    item: a string indicating the gbf item hidden behind the button
    row: an integer indicating on what row to set the button on
    label: the default string label on the button
    style: the default Discord button style
    """
    def __init__(self, item : str, row : int, label : str = '???', style : disnake.ButtonStyle = disnake.ButtonStyle.secondary):
        super().__init__(style=style, label='\u200b', row=row)
        self.item = item
        self.label = label

    """callback()
    Coroutine callback called when the button is called
    Stop the view when the game is won
    
    Parameters
    ----------
    interaction: a Discord interaction
    """
    async def callback(self, interaction: disnake.Interaction):
        self.view.update_last(interaction)
        if not self.disabled and self.view.ownership_check(interaction):
            self.disabled = True
            self.label = self.item
            self.style = disnake.ButtonStyle.primary
            if self.view.check_status(self.item):
                self.view.stopall()
                await interaction.response.edit_message(embed=self.view.bot.util.embed(author={'name':"{} scratched".format(interaction.user.display_name), 'icon_url':interaction.user.display_avatar}, description="You won **{}**".format(self.item), thumbnail='http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/' + self.view.thumbs.get(self.item, ''), footer=self.view.footer, color=self.view.color), view=self.view)
                await self.view.bot.util.clean(interaction, 70)
            else:
                await interaction.response.edit_message(view=self.view)
        else:
            await interaction.response.send_message("You can't press this button", ephemeral=True)

class Scratcher(BaseView):
    """__init__()
    Constructor
    
    Parameters
    ----------
    bot: a pointer to the bot for ease of access
    owner_id: the id of the user responsible for the interaction, leave to None to ignore
    grid: a 10 items-list to be hidden behind the buttons
    thumbs: the dict matching the item thumbnail
    color: the color to be used for the message embed
    footer: the footer to be used for the message embed
    """
    def __init__(self, bot, owner_id : int, grid, thumbs : dict, color : int, footer : str):
        super().__init__(bot, owner_id=owner_id, timeout=80.0)
        self.grid = grid
        self.thumbs = thumbs
        self.color = color
        self.footer = footer
        self.state = {}
        self.counter = 0
        for i in range(9):
            self.add_item(ScratcherButton(self.grid[i], i // 3))

    """check_status()
    Function to check the game state
    
    Parameters
    ----------
    item: the last item revealed behind a button
    
    Returns
    --------
    bool: True if the game is over, False if not
    """
    def check_status(self, item):
        self.counter += 1
        if item not in self.state: self.state[item] = 0
        self.state[item] += 1
        game_over = (self.state[item] == 3)
        for c in self.children:
            if c.disabled:
                if self.state.get(c.item, 0) == 2: c.style = disnake.ButtonStyle.success
                elif self.state.get(c.item, 0) == 3: c.style = disnake.ButtonStyle.danger
            elif game_over:
                self.state[c.item] = self.state.get(c.item, 0) + 1
                for e in self.children:
                    e.label = e.item
                    e.disabled = True
        if not game_over and self.counter == 9:
            self.add_item(ScratcherButton(self.grid [9], 3, 'Final Scratch', disnake.ButtonStyle.danger))
        return game_over