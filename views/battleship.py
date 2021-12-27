from . import BaseView
import disnake
import random

# ----------------------------------------------------------------------------------------------------------------
# BattleShip View
# ----------------------------------------------------------------------------------------------------------------
# View class used to play Battle Ship
# ----------------------------------------------------------------------------------------------------------------

class BattleShipButton(disnake.ui.Button):
    """__init__()
    Button Constructor
    
    Parameters
    ----------
    btype: 0 for column buttons, 1 for row buttons
    target: string, target of the button (ABCDE or 12345)
    row: an integer indicating on what row to set the button on
    """
    def __init__(self, btype : int, target : str, row : int):
        super().__init__(style=(disnake.ButtonStyle.success if btype == 0 else disnake.ButtonStyle.danger), label=target, row=row)
        self.btype = btype
        self.target = target

    """callback()
    Coroutine callback called when the dropdown is used
    Stop the view when the game is won
    
    Parameters
    ----------
    interaction: a disnake interaction
    """
    async def callback(self, interaction: disnake.Interaction):
        if self.view.state >= 0 and self.view.players[self.view.state].id == interaction.user.id:
            self.view.input[self.btype] = self.target
            if None not in self.view.input:
                res = self.view.shoot("".join(self.view.input))
                if res == 0:
                    await interaction.response.send_message("You can't shoot at {}".format("".join(self.view.input)), ephemeral=True)
                else:
                    self.view.notification = "{} shot at **{}**\n".format(self.view.players[self.view.state].display_name, "".join(self.view.input))
                    self.view.input = [None, None]
                    if res == 2:
                        self.view.notification += "**{}** is the winner".format(self.view.players[self.view.state].display_name)
                        self.view.state = -1
                    else:
                        self.view.state = (self.view.state + 1) % 2
                        self.view.notification += "Turn of **{}**".format(self.view.players[self.view.state].display_name)
                    if self.view.state < 0:
                        self.view.stopall()
                        self.disabled = True
                    await self.view.update(interaction)
            else:
                extra_notif = "\n{} is selecting **".format(self.view.players[self.view.state].display_name)
                extra_notif += ('?' if self.view.input[0] is None else self.view.input[0])
                extra_notif += ('?' if self.view.input[1] is None else self.view.input[1])
                extra_notif += "**..."
                await self.view.update(interaction, extra_notif=extra_notif)
        else:
            await interaction.response.send_message("It's not your turn to play or you aren't the player", ephemeral=True)

class BattleShip(BaseView):
    """__init__()
    Constructor
    
    Parameters
    ----------
    bot: a pointer to the bot for ease of access
    players: list of Players
    embed: disnake.Embed to edit
    """
    def __init__(self, bot, players : list, embed : disnake.Embed):
        super().__init__(bot, timeout=420)
        self.grids = [[0 for i in range(20)] + [10 for i in range(5)], [0 for i in range(20)] + [10 for i in range(5)]]
        random.shuffle(self.grids[0])
        random.shuffle(self.grids[1])
        self.state = 0
        self.players = players
        self.embed = embed
        self.input = [None, None]
        for i in ['A', 'B', 'C', 'D', 'E']:
            self.add_item(BattleShipButton(0, i, 0))
        for i in range(5):
            self.add_item(BattleShipButton(1, str(i+1), 1))
        self.notification = "Turn of **{}**".format(self.players[self.state].display_name)

    """update()
    Update the embed
    
    Parameters
    ----------
    inter: an interaction
    init: if True, it uses a different method (only used from the command call itself)
    extra_notif: optional string to append to the embed description
    """
    async def update(self, inter, init=False, extra_notif=""):
        self.embed.description = ":ship: {} :cruise_ship: {}\n".format(self.players[0].display_name, self.players[1].display_name) + self.notification + extra_notif
        for i in range(0, 2):
            self.embed.set_field_at(i, name=self.players[i].display_name, value=self.render(i))
        if init: await inter.edit_original_message(embed=self.embed, view=self)
        elif self.state >= 0: await inter.response.edit_message(embed=self.embed, view=self)
        else: await inter.response.edit_message(embed=self.embed, view=None)

    """shoot()
    Try to shoot at a location
    
    Parameters
    ----------
    value: string value sent by the dropdown (example: "C3")
    
    Return
    ----------
    int: 2 if the game is won, 1 if the value is valid, 0 if not
    """
    def shoot(self, value):
        x = 0
        y = int(value[1]) - 1
        opponent = (self.state + 1) % 2
        match value[0]:
            case 'A': x = 0
            case 'B': x = 1
            case 'C': x = 2
            case 'D': x = 3
            case 'E': x = 4
        if self.grids[opponent][x + y * 5] % 10 == 0:
            self.grids[opponent][x + y * 5] += 1
            if 10 not in self.grids[opponent]: return 2
            return 1
        return 0

    """render()
    Render one of the grid into a string
    
    Parameters
    ----------
    grid_id: integer, either 0 (first player) or 1 (second)
    
    Return
    ----------
    str: resulting string
    """
    def render(self, grid_id):
        msg = ":white_square_button::regional_indicator_a::regional_indicator_b::regional_indicator_c::regional_indicator_d::regional_indicator_e:\n"
        for r in range(5):
            match r:
                case 0: msg += ":one:"
                case 1: msg += ":two:"
                case 2: msg += ":three:"
                case 3: msg += ":four:"
                case 4: msg += ":five:"
            for c in range(5):
                match self.grids[grid_id][c + r * 5]:
                    case 0: msg += ":blue_square:"
                    case 10:
                        if self.state >= 0: msg += ":blue_square:"
                        else: msg += ":cruise_ship:"
                    case 1:
                        msg += ":purple_square:"
                    case 11:
                        msg += ":boom:"
            msg += "\n"
        return msg