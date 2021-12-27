from . import BaseView
import disnake

# ----------------------------------------------------------------------------------------------------------------
# ConnectFour View
# ----------------------------------------------------------------------------------------------------------------
# View class used to play Connect Four
# ----------------------------------------------------------------------------------------------------------------

class ConnectFourButton(disnake.ui.Button):
    """__init__()
    Button Constructor
    
    Parameters
    ----------
    column: Corresponding column in the grid (0 - 6)
    """
    def __init__(self, column : int):
        super().__init__(style=disnake.ButtonStyle.primary, label='{}'.format(column+1))
        self.column = column

    """callback()
    Coroutine callback called when the button is called
    Stop the view when the game is won
    
    Parameters
    ----------
    interaction: a disnake interaction
    """
    async def callback(self, interaction: disnake.Interaction):
        if self.view.state >= 0 and self.view.players[self.view.state].id == interaction.user.id and self.view.grid[self.column] == 0:
            self.view.insert(self.column)
            self.view.notification = "{} played in column **{}**\n".format(self.view.players[self.view.state].display_name, self.column+1)
            if self.view.checkWin():
                self.view.notification += "**{}** is the winner".format(self.view.players[self.view.state].display_name)
                self.view.state = -1
            elif 0 not in self.view.grid:
                self.view.notification += "It's a **Draw**..."
                self.view.state = -1
            else:
                self.view.state = (self.view.state + 1) % 2
                self.view.notification += "Turn of **{}**".format(self.view.players[self.view.state].display_name)
            if self.view.state < 0:
                self.view.stopall()
            elif self.view.grid[self.column] != 0:
                self.disabled = True
            await self.view.update(interaction)
        else:
            await interaction.response.send_message("It's not your turn to play or you aren't the player", ephemeral=True)

class ConnectFour(BaseView):
    """__init__()
    Constructor
    
    Parameters
    ----------
    bot: a pointer to the bot for ease of access
    players: list of Players
    embed: disnake.Embed to edit
    """
    def __init__(self, bot, players : list, embed : disnake.Embed):
        super().__init__(bot, timeout=480)
        self.grid = [0 for i in range(6*7)]
        self.state = 0
        self.players = players
        self.embed = embed
        for i in range(7): self.add_item(ConnectFourButton(i))
        self.notification = "Turn of **{}**".format(self.players[self.state].display_name)

    """update()
    Update the embed
    
    Parameters
    ----------
    inter: an interaction
    init: if True, it uses a different method (only used from the command call itself)
    """
    async def update(self, inter, init=False):
        self.embed.description = ":red_circle: {} :yellow_circle: {}\n".format(self.players[0].display_name, self.players[1].display_name) + self.notification + "\n" + self.render()
        if init: await inter.edit_original_message(embed=self.embed, view=self)
        elif self.state >= 0: await inter.response.edit_message(embed=self.embed, view=self)
        else: await inter.response.edit_message(embed=self.embed, view=None)

    """insert()
    Insert a piece in the grid
    
    Parameters
    ----------
    pos: Column to insert to (note: it must have been checked previously for empty spaces)
    """
    def insert(self, pos):
        mem = pos
        for i in range(1, 6):
            if self.grid[pos + 7 * i] != 0: break
            mem = pos + 7 * i
        self.grid[mem] = self.state + 1

    """checkWin()
    Check if the current player won
    
    Return
    ----------
    bool: True if won, False if not
    """
    def checkWin(self):
        piece = self.state + 1
        for c in range(4):
            for r in range(6):
                if self.grid[c + r * 7] == piece and self.grid[c + 1 + r * 7] == piece and self.grid[c + 2 + r * 7] == piece and self.grid[c + 3 + r * 7] == piece:
                    return True
        for c in range(7):
            for r in range(3):
                if self.grid[c + r * 7] == piece and self.grid[c + (r + 1) * 7] == piece and self.grid[c + (r + 2) * 7] == piece and self.grid[c + (r + 3) * 7] == piece:
                    return True
        for c in range(4):
            for r in range(3):
                if self.grid[c + r * 7] == piece and self.grid[c + 1 + (r + 1) * 7] == piece and self.grid[c + 2 + (r + 2) * 7] == piece and self.grid[c + 3 + (r + 3) * 7] == piece:
                    return True
        for c in range(4):
            for r in range(3, 6):
                if self.grid[c + r * 7] == piece and self.grid[c + 1 + (r - 1) * 7] == piece and self.grid[c + 2 + (r - 2) * 7] == piece and self.grid[c + 3 + (r - 3) * 7] == piece:
                    return True
        return False

    """render()
    Render the grid into a string
    
    Return
    ----------
    str: resulting string
    """
    def render(self):
        msg = ""
        for r in range(6):
            for c in range(7):
                msg += "{} ".format(self.grid[c + r * 7])
            msg += "\n"
        return msg.replace('0 ', ':blue_circle:').replace('1 ', ':red_circle:').replace('2 ', ':yellow_circle:') + ":one::two::three::four::five::six::seven:"