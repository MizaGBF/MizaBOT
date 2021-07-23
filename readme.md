# MizaBOT  
* [Granblue Fantasy](http://game.granbluefantasy.jp) Discord Bot.  
* Command List available [Here](https://mizagbf.github.io/MizaBOT/).  
### Requirements  
* Python 3.9.  
* [discord.py](https://github.com/Rapptz/discord.py) (formerly the rewrite branch).  
* [PyDrive2](https://github.com/iterative/PyDrive2) to access the google drive where the save file is stored.  
* [psutil](https://psutil.readthedocs.io/en/latest/).  
* [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/).  
* [Tweepy](https://github.com/tweepy/tweepy).  
* [Pillow](https://pillow.readthedocs.io/en/stable/).  
* [leather](https://pypi.org/project/leather/).  
* [CairoSVG](https://pypi.org/project/CairoSVG/).  
* `pip install -r requirements.txt` to install all the modules.  
### Version 8.0  
This version is currently in Beta.
More changes and improvements will come once discord.py 2.0 get released.
### Informations  
MizaBOT is a Discord Bot themed around the game [Granblue Fantasy](http://game.granbluefantasy.jp).  
It features a lot of useful utility commands, including some advanced features, for a total of **over 130 commands**.  
Check the [Command List](https://mizagbf.github.io/MizaBOT/) for details.  
  
It's designed to be used on [Heroku](https://www.heroku.com) and isn't intended to be setup and used by anyone. Still, if you are interested, details are available on the [Wiki](https://github.com/MizaGBF/MizaBOT/wiki) and in this [issue](https://github.com/MizaGBF/MizaBOT/issues/1).  
  
The bot is semi open to invitations:  
[![Invitation](https://github.com/MizaGBF/MizaBOT/raw/master/docs/img/invite.png)](https://discordapp.com/oauth2/authorize?client_id=614723060100104193&scope=bot&permissions=1074252864)  
Currently only servers of 30 members or more can be added to limit the number of new servers.  
You'll have to wait for my owner approval (Your server owner will be notified if accepted).  
Misuses of this link will result in a server-wide ban.  
I have limited resources so I reserve to myself the right to refuse your server, sorry in advance.  
  
### Code Overview  
* The bot is divided in three parts:
  * The client itself in [bot.py](https://github.com/MizaGBF/MizaBOT/blob/master/bot.py)  
  * The [components](https://github.com/MizaGBF/MizaBOT/tree/master/components), which features various utility functions for the bot well being   
  * The [cogs](https://github.com/MizaGBF/MizaBOT/tree/master/cogs), where you can find all the user commands
* All data (from the config and save files) are centralized in the Data component and are accessible by the Bot, Cogs or other Components at any time.  
* A "Graceful Exit" is needed for a proper use on [Heroku](https://www.heroku.com). A `SIGTERM` signal is sent when a restart happens on the [Heroku](https://www.heroku.com) side (usually every 24 hours, when you push a change or in some other cases). If needed, the bot also saves when this happens.  
Check the `exit_gracefully()` function for details.  
* During the boot, all the .py files in the cogs folder are tested to find valid cogs.  

### Features  
* Get detailed informations on the game status from Discord  
![GBF command](https://cdn.discordapp.com/attachments/614716155646705676/858731441316036638/unknown.png)
![Gacha command](https://cdn.discordapp.com/attachments/614716155646705676/858731761131323392/unknown.png)
* Manage and estimate your next Granblue Spark  
![SeeRoll command](https://cdn.discordapp.com/attachments/614716155646705676/858729482386145310/unknown.png)
* Find and search in-game profiles and crews  
![Profile command](https://cdn.discordapp.com/attachments/614716155646705676/858730610260443196/unknown.png)
* Search the [wiki](https://gbf.wiki/) directly from Discord  
![Wiki command](https://cdn.discordapp.com/attachments/614716155646705676/858730975025954875/unknown.png)
* Get Unite and Fight detailed informations  
![Estim command](https://cdn.discordapp.com/attachments/614716155646705676/858732302635892766/unknown.png)
![Ranking command](https://cdn.discordapp.com/attachments/614716155646705676/858732645869551646/unknown.png)
![Findplayer command](https://cdn.discordapp.com/attachments/614716155646705676/858733133879574559/unknown.png)
![Findcrew command](https://cdn.discordapp.com/attachments/614716155646705676/858733490480873514/unknown.png)
* ~~Salty~~ Fun Game commands  
![Spark command](https://cdn.discordapp.com/attachments/614716155646705676/858733892926963732/unknown.png)
![Roulette command](https://cdn.discordapp.com/attachments/614716155646705676/858734003560251422/unknown.png)
![Scratcher command](https://cdn.discordapp.com/attachments/614716155646705676/858734170222362664/unknown.png)
* And much more... Consult the [command list](https://mizagbf.github.io/MizaBOT/) for details.  