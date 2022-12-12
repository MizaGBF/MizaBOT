# Important  
The project has been discontinued.  
More details [here](https://twitter.com/mizak0/status/1571202365641875456).  
  
*12/12/2022*: A privately hosted closed-source exists under the name [Rosetta](https://github.com/MizaGBF/Rosetta-Public), from which I backported some of the fixes to MizaBOT for the version named 9.99.  

# MizaBOT  
* [Granblue Fantasy](https://game.granbluefantasy.jp) Discord Bot.  
* Command List and Help available [Here](https://mizagbf.github.io/MizaBOT/).  

[![CodeQL](https://github.com/MizaGBF/MizaBOT/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/MizaGBF/MizaBOT/actions/workflows/codeql-analysis.yml)[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)  
### Requirements  
* Python 3.10.  
* [Disnake](https://github.com/DisnakeDev/disnake).  
* [PyDrive2](https://github.com/iterative/PyDrive2) to access the google drive where the save file is stored.  
* [psutil](https://psutil.readthedocs.io/en/latest/).  
* [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/).  
* [Tweepy](https://github.com/tweepy/tweepy).  
* [Pillow](https://pillow.readthedocs.io/en/stable/).  
* [httpx](https://www.python-httpx.org/).  
* [uvloop](https://github.com/MagicStack/uvloop) (UNIX only).  
* `pip install -r requirements.txt` to install all the modules.  
  
### Informations  
MizaBOT is a Discord Bot themed around the game [Granblue Fantasy](https://game.granbluefantasy.jp).  
It features a lot of useful utility commands, including some advanced features, for a total of **over 120 commands**.  
Check the [Online Help](https://mizagbf.github.io/MizaBOT/) for details.  
  
It's designed to be used on [Heroku](https://www.heroku.com) and isn't intended to be setup and used by anyone. Still, if you are interested, details are available on the [Wiki](https://github.com/MizaGBF/MizaBOT/wiki) and in this [issue](https://github.com/MizaGBF/MizaBOT/issues/1).  
  
### Features  
*(The following screenshots were taken on version 9.13)*  
* Get detailed informations on the game status from Discord  
![/gbf info](https://media.discordapp.net/attachments/614716155646705676/934039092180713472/unknown.png)
![/gbf gacha](https://media.discordapp.net/attachments/614716155646705676/934039127404449802/unknown.png)
* Manage and estimate your next Granblue Spark  
![/spark see](https://media.discordapp.net/attachments/614716155646705676/934039488999616602/unknown.png)
* Find and search in-game profiles and crews  
![/gbf profile](https://media.discordapp.net/attachments/614716155646705676/934039850619920384/unknown.png)
* Search the [wiki](https://gbf.wiki/) directly from Discord  
![/gbf wiki](https://media.discordapp.net/attachments/614716155646705676/934040026126356510/unknown.png)
* Get Unite and Fight detailed informations  
![/gw estimation](https://media.discordapp.net/attachments/614716155646705676/934040181244309584/unknown.png)
![/gw ranking](https://media.discordapp.net/attachments/614716155646705676/934040124617007124/unknown.png)
![/gw find player](https://media.discordapp.net/attachments/614716155646705676/934040315835322398/unknown.png)
![/gw find crew](https://media.discordapp.net/attachments/614716155646705676/934040684355268638/unknown.png)
* ~~Salty~~ Fun Game commands  
![/roll spark](https://media.discordapp.net/attachments/614716155646705676/934040932850995210/unknown.png)
![/game scratch](https://media.discordapp.net/attachments/614716155646705676/934041270584766474/unknown.png)
* And much more... Consult the [command list](https://mizagbf.github.io/MizaBOT/) for details.  