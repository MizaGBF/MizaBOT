from . import BaseView
import disnake

# ----------------------------------------------------------------------------------------------------------------
# Url Button View
# ----------------------------------------------------------------------------------------------------------------
# View class used to open urls
# ----------------------------------------------------------------------------------------------------------------

class UrlButton(BaseView):
    """__init__()
    Constructor
    
    Parameters
    ----------
    bot: a pointer to the bot for ease of access
    urls: list of urls and the button label (string, string) to make into button
    """
    def __init__(self, bot, urls : list):
        super().__init__(bot)
        if len(urls) == 0: raise Exception("Empty url list")
        for u in urls:
            self.add_item(disnake.ui.Button(style=disnake.ButtonStyle.link, label=u[0], url=u[1]))