from . import BaseView
import disnake

# ----------------------------------------------------------------------------------------------------------------
# TicTacToe View
# ----------------------------------------------------------------------------------------------------------------
# View class used to play Tic Tac Toe
# ----------------------------------------------------------------------------------------------------------------

class TicTacToeButton(disnake.ui.Button):
    """__init__()
    Button Constructor
    
    Parameters
    ----------
    pos: Integer position in grid (0 - 9)
    v: default value of the button (0: unused, 1: X, 2: O
    """
    def __init__(self, pos : int, v : int):
        super().__init__(style=disnake.ButtonStyle.secondary, label='\u200b', row=pos // 3)
        match v:
            case 1:
                self.style = disnake.ButtonStyle.success
                self.label = "X"
                self.disabled = True
            case 2:
                self.style = disnake.ButtonStyle.danger
                self.label = "O"
                self.disabled = True
        self.pos = pos

    """callback()
    Coroutine callback called when the button is called
    Stop the view when the game is won
    
    Parameters
    ----------
    interaction: a disnake interaction
    """
    async def callback(self, interaction: disnake.Interaction):
        if not self.disabled and interaction.user.id == self.view.playing.id and self.view.grid[self.pos] == 0:
            self.disabled = True
            self.view.grid[self.pos] = self.view.playing_index + 1
            if self.view.playing_index == 0:
                self.style = disnake.ButtonStyle.success
                self.label = "X"
            else:
                self.style = disnake.ButtonStyle.danger
                self.label = "O"
            state = self.view.check_status()
            self.view.embed.description = ":x: {} :o: {}\n{}".format(self.view.players[0].display_name, self.view.players[1].display_name, self.view.notification)
            if state:
                self.view.stopall()
                await interaction.response.edit_message(embed=self.view.embed, view=self.view)
            else:
                await interaction.response.edit_message(embed=self.view.embed, view=self.view)
        else:
            await interaction.response.send_message("It's not your turn to play", ephemeral=True)

class TicTacToe(BaseView):
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
        self.players = players
        self.embed = embed
        self.playing = self.players[0]
        self.playing_index = 0
        self.grid = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.moves = 0
        self.win_state = [
            [0,1,2],
            [3,4,5],
            [6,7,8],
            [0,3,6],
            [1,4,7],
            [2,5,8],
            [0,4,8],
            [2,4,6]
        ]
        self.notification = "Turn of {}".format(self.playing.display_name)
        for i in range(9):
            self.add_item(TicTacToeButton(i, self.grid[i]))

    """state()
    Return if the game is won or not
    
    Returns
    --------
    typle: (win boolean, id of the winning player)
    """
    def state(self):
        for w in self.win_state:
            if self.grid[w[0]] != 0 and self.grid[w[0]] == self.grid[w[1]] and self.grid[w[0]] == self.grid[w[2]]:
                return True, self.grid[w[0]] - 1
        return False, None

    """evaluate()
    Minimax function for the AI to calculate the optimal move
    
    Parameters
    ----------
    depth: number of iterations left, shouldn't be higher than the number of moves left
    index: 0 for Player 1, 1 for MizaBOT
    alpha: integer used for earching the best move
    beta: integer used for earching the best move
    
    Returns
    --------
    list: [position, score]
    """
    def evaluate(self, depth, index, alpha : int = -9999999, beta : int = 9999999):
        state = self.state()
        if depth == 0 or state[0]:
            return [-1, (-1 if state[1] == self.bot_id else 1)]        
        
        v_eval = (9999999 if index == self.bot_id else -9999999)
        for i in range(len(self.grid)):
            if self.grid[i] != 0: continue
            self.grid[i] = index + 1
            score = self.evaluate(depth - 1, (index + 1) % 2, alpha, beta)
            if (index == self.bot_id and score[1] < v_eval) or (index != self.bot_id and score[1] > v_eval):
                v_eval = score[1]
                best_move = i
            self.grid[i] = 0
            if index == self.bot_id: beta = min(beta, score[1])
            else: beta = max(beta, score[1])
            if beta <= alpha:
                break
        return [best_move, v_eval]

    """check_status()
    Function to check the game state
    
    Returns
    --------
    bool: True if the game is over, False if not
    """
    def check_status(self):
        self.moves += 1
        won = False
        win_id = None
        won, win_id = self.state()
        if won or self.moves == 9:
            if win_id is not None:
                self.playing = self.players[win_id]
                self.playing_index = win_id
                self.notification = "**{}** is the winner".format(self.playing.display_name)
            else:
                self.notification = "It's a **Draw**..."
            for c in self.children:
                c.disabled = True
            return True
        else:
            self.playing_index = (self.playing_index + 1) % 2
            self.playing = self.players[self.playing_index]
            self.notification = "Turn of **{}**".format(self.playing.display_name)
            return False