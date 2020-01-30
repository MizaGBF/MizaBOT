# MizaBOT  
* [Granblue Fantasy](http://game.granbluefantasy.jp) Discord Bot used by the /gbfg/ server.  
#### Requirements  
* Python 3.8.  
* [discord.py](https://github.com/Rapptz/discord.py) (formerly the rewrite branch).  
* [PyDrive](https://pythonhosted.org/PyDrive/) to access the google drive where the save file is stored.  
* [psutil](https://psutil.readthedocs.io/en/latest/).  
* [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/).  
* `pip install -r requirements.txt` to install all the modules.  
### Setup  
The bot is designed to be used on [Heroku](https://www.heroku.com).  
Here are a few instructions to set it up in its current state:  
* On the [Heroku](https://www.heroku.com) side, you only need to create a new app. The [CLI](https://devcenter.heroku.com/articles/heroku-cli) might help if you intend to do a git push since your own computer.   
* The bot uses [Google Drive](https://www.google.com/drive/) to read and save its data. You'll need to get API keys from [Google](https://developers.google.com/drive) and fill the `settings.yaml` you can find in the [example folder](https://github.com/MizaGBF/MizaBOT/tree/master/example).  
* Finally, you also need your [Discord token](https://discordapp.com/developers/applications/).  
* Other files in the [example folder](https://github.com/MizaGBF/MizaBOT/tree/master/example) are:  
* `config.json` must be edited with a notepad (follow the instructions inside) and placed with the bot code (your discord token must be inserted inside).  
* `save.json` can be used as it is and must be placed in the [Google Drive](https://www.google.com/drive/) folder used to save the bot data. The bot can't start without a valid save file.  
This [issue](https://github.com/MizaGBF/MizaBOT/issues/1) might help if you encounter a problem.  
Example files might be a bit outdated. I'll do my best to update them as much as possible.  
### Code Overview  
* [asyncio](https://docs.python.org/3/library/asyncio.html) is used by [discord.py](https://github.com/Rapptz/discord.py), there is no multithreading involved in this bot as a result. Which means a function must not hog all the cpu time.  
* Data (from the config or save file) is centralized on the Bot instance and accessible by the Cogs at any time.  
* The bot checks the `savePending` variable every 20 minutes in the `statustask()` function and save to the drive if True.  
* The `GracefulExit` is needed for a proper use on [Heroku](https://www.heroku.com). A `SIGTERM` signal is sent when a restart happens on the [Heroku](https://www.heroku.com) side (usually every 24 hours, when you push a change or in some other cases). The bot also checks the `savePending` variable when this happens.  
* You can change which cog is loaded at the end of `bot.py`, at the `loadCog()` line.  
* `baguette.py` is my personal cog and won't ever be on this github, you can safely remove it from the `loadCog()` call.  
* The debug channel refers to a channel, in my test server, where the bot send debug and error messages while running. Useful when I can't check the logs on Heroku.  
* Cogs are found in the [cogs folder](https://github.com/MizaGBF/MizaBOT/tree/master/cogs) and sort functions by their purpose.  
### User Overview  
* The default command prefix is `$`. It can be changed using the `$setPrefix <your new prefix>` command.  
* `$help` sends the accessible command list to your private messages. Check your privacy settings if the bot can't send you a direct message. You can also do `$help <command name>` or `$help <cog name>` to get details or just the commands of a specific cog.  
![Privacy example](https://cdn.discordapp.com/attachments/614716155646705676/643427911063568426/read02.png)
* A bot sees an user with the manage messages permission as a server moderator, in the channel where the command is invoked. So, be careful with this.  
* If you don't want to put the bot in quarantine in a single channel, you can disable the most "annoying" commands using `$toggleFullBot` in the concerned channel. `$allowBotEverywhere` lets you reset everything, while `$seeBotPermission` shows you all the allowed channels.  
![Command example](https://cdn.discordapp.com/attachments/614716155646705676/643427915526045696/read03.png)
* `$toggleBroadcast` and `$seeBroadcast` works the same. If the bot owner needs to send a message to all servers, those channels will receive the message.  
* Servers need to be approved before the bot can be used in it. The owner must use the `$accept <server id>` or `$refuse <server id>` commands. `$ban_server <server id>` or `$ban_owner <owner id>` can be used to forbid someone to add the bot to a server. The owner's 'debug server' registered in `config.json` can bypass those restrictions.  
* The [Granblue Fantasy](http://game.granbluefantasy.jp) Schedule must be manually set using `$setschedule`. The syntax is the following: `$setschedule date of event 1;name of event 1; etc.... ; date of event N; name of event N`. The previous command can be retrieved using `$schedule raw`.  
![Schedule example](https://cdn.discordapp.com/attachments/614716155646705676/643427910874693642/read01.png)
* For details on everything else, I recommend the `$help` command.  
