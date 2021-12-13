from . import BaseView
import disnake
import asyncio
from datetime import datetime, timedelta

# ----------------------------------------------------------------------------------------------------------------
# Poll View
# ----------------------------------------------------------------------------------------------------------------
# View class used to make polls
# ----------------------------------------------------------------------------------------------------------------

class PollDropdown(disnake.ui.Select):
    """__init__()
    Constructor
    
    Parameters
    ----------
    title: poll title string
    choices: list of the poll choices (strings)
    """
    def __init__(self, title : str = "", choices : list = []):
        options = []
        for c in choices:
            options.append(disnake.SelectOption(label=c))
        if len(options) < 2: raise Exception('Please specify what to poll for\nFormat: `duration title;choice1;choice2;...;choiceN`')
        super().__init__(placeholder=title, min_values=1, max_values=1, options=options)

    """callback()
    Coroutine callback called when the dropdown is used
    
    Parameters
    ----------
    interaction: a Discord interaction
    """
    async def callback(self, interaction: disnake.Interaction):
        self.view.update_last(interaction)
        self.view.votes[interaction.user.id] = self.values[0]
        await interaction.response.send_message(f'Vote updated to `{self.values[0]}`', ephemeral=True)


class Poll(BaseView):
    """__init__()
    Constructor
    
    Parameters
    ----------
    bot: a pointer to the bot for ease of access
    author: user object of the poll creator
    color: integer used for the embed color
    title: pool title string
    choices: list of the poll choices (strings)
    """
    def __init__(self, bot, author, color : int, title : str = "", choices : list = []):
        super().__init__(bot, timeout=None, enable_timeout_cleanup=False)
        self.author = author
        self.color = color
        self.title = title
        self.votes = {}
        self.choices = []
        choices.reverse()
        while len(choices) > 0:
            c = choices.pop()
            if c in choices or c == "": continue
            self.choices.append(c)

        self.add_item(PollDropdown(title, self.choices))

    """run_poll()
    Countdown for X seconds before returning the poll result
    
    Parameters
    ----------
    duration: poll duration in seconds
    message: original message to update
    channel: where to post the results
    """
    async def run_poll(self, duration : int, message : disnake.Message, channel : disnake.TextChannel):
        timer = self.bot.util.JST() + timedelta(seconds=duration)
        author={'name':'{} started a poll'.format(self.author.display_name), 'icon_url':self.author.display_avatar}
        while True:
            await asyncio.sleep(1)
            c = self.bot.util.JST()
            if c >= timer: break
            await message.edit(embed=self.bot.util.embed(author=author, title=self.title, description="{} seconds remaining to vote\n{} participants".format((timer - c).seconds, len(self.votes)), color=self.color))
        self.stopall()
        await message.delete()
        msg = "**{}** vote(s)\n".format(len(self.votes))
        count = {}
        for c in self.choices:
            count[c] = 0
        for id in self.votes:
            if self.votes[id] in count: count[self.votes[id]] += 1
        for v in count:
            msg += "`{}` :white_small_square: {}\n".format(v, count[v])
        await channel.send(embed=self.bot.util.embed(author={'name':"{}'s poll ended".format(self.author.display_name), 'icon_url':self.author.display_avatar}, title=self.title, description=msg, color=self.color))