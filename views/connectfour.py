from . import BaseView
import disnake
import asyncio
import random

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
        super().__init__(style=disnake.ButtonStyle.primary, label="{}".format(column+1))
        self.column = column


    """callback()
    Coroutine callback called when the button is called
    Stop the view when the game is won
    
    Parameters
    ----------
    interaction: a disnake interaction
    """
    async def callback(self, interaction: disnake.Interaction):
        if not self.disabled and self.view.ownership_check(interaction):
            d = self.pos - 16
            if d >= 0 or d < 4:
                self.view.state = self.view.move_2048(d)
                self.view.update_button()
                if self.view.state[0] == True:
                    self.view.embed.description.replace("is playing...", "won :confetti_ball:")
                elif self.view.state[1] == False:
                    self.view.embed.description.replace("is playing...", "lost :pensive:")
                self.view.embed.footer.text = "{} moves".format(self.view.move)
            await interaction.response.edit_message(embed=self.view.embed, view=self.view)
        else:
            await interaction.response.send_message("You aren't the player", ephemeral=True)

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
        super().__init__(bot, timeout=500)
        self.grid = [0 for i in range(6*7)]
        self.state = 0
        self.players = players
        self.embed = embed
        for i in range(7): self.add_item(ConnectFourButton(i))
        self.notification = "Turn of {}".format(self.players[self.state].display_name)

    async def update(self):
        self.embed.description = self.notification + "\n" + self.render()

    def run(self): # test
        self.display()
        if self.state == self.ai:
            # play
            self.state = 1
        while self.state >= 0:
            while True:
                try:
                    r = int(input("Input column (0-6):"))
                    if r < 0 or r > 6 or self.grid[r] != 0: raise Exception()
                    break
                except:
                    pass
            self.insert(r)
            if self.checkWin():
                print("Player", self.state+1, "won")
                self.state = -1
            elif 0 not in self.grid:
                print("Draw")
                self.state = -1
            else:
                self.state = (self.state + 1) % 2
            if self.state == self.ai:
                # play
                if self.checkWin():
                    print("Player", self.state+1, "won")
                    self.state = -1
                elif 0 not in self.grid:
                    print("Draw")
                    self.state = -1
                else:
                    self.state = (self.state + 1) % 2
            self.display()
        

    def insert(self, pos):
        mem = pos
        for i in range(1, 6):
            if self.grid[pos + 7 * i] != 0: break
            mem = pos + 7 * i
        self.grid[mem] = self.state + 1

    def checkWin(self):
        piece = self.state + 1
        for c in range(4):
            for r in range(6):
                if self.grid[c + r] == piece and self.grid[c + 1 + r * 7] == piece and self.grid[c + 2 + r * 7] == piece and self.grid[c + 3 + r * 7] == piece:
                    return True
        for c in range(7):
            for r in range(3):
                if self.grid[c + r * 7] == piece and self.grid[c + (r + 1) * 7] == piece and self.grid[c + (r + 2) * 7] == piece and self.grid[c + (r + 3) * 7] == piece:
                    return True
        for c in range(4):
            for r in range(3):
                if self.grid[c + r * 7] == piece and self.grid[c + 1 + (r + 1) * 7] == piece and self.grid[c + 2 + (r + 2) * 7] == piece and self.grid[c + 2 + (r + 2) * 7] == piece:
                    return True
        for c in range(4):
            for r in range(3, 6):
                if self.grid[c + r * 7] == piece and self.grid[c + 1 + (r - 1) * 7] == piece and self.grid[c + 2 + (r - 2) * 7] == piece and self.grid[c + 3 + (r - 3) * 7] == piece:
                    return True
        return False

    def render(self):
        msg = ""
        for r in range(6):
            for c in range(7):
                msg += "{} ".format(self.grid[c + r * 7])
            msg += "\n"
        return msg.replace('0 ', ':blue_circle:').replace('1 ', ':red_circle:').replace('2 ', ':yellow_circle:')