== INSTALLATION ==
1) Download and Install Python 3.8 https://www.python.org/ or newer.
2) During the installation, leave the "install tkinter/ttk" (or similar) enabled.
3) You are done. Necessary packages will be installed the first time you launch the app.

If you want to do it manually, run in a command prompt this command:
python -m pip install -r requirements.txt

== UPDATE THE PACKAGES ==
Just rerun the
python -m pip install -r requirements.txt
command on a newer version, I'll update the file if needed.

== AUTHENTIFICATION ==
A Twitter account is required to use this application. Two ways exist:
1) If you are registered as a developper, go to https://developer.twitter.com/, create an app and fill 'gbfraidcopier.cfg' with the consumer and access tokens. You can also apply here: https://developer.twitter.com/en/apply/account
2) If not, your Web Browser will open, asking you to authorize the application. Give the PIN code to the raidfinder it will generate your tokens for future uses.

== USAGE ==
Just double click on 'gbfraidcopier.pyw', assuming you installed everything properly
Alternatively on Windows, shift+right click in the folder > "Open a command prompt here" > type the command "python gbfraidcopier.pyw" without the quotes. If python isn't in your PATH, you need to write its full path instead of just "python", like during the installation process.

== BLACKLIST ==
If you need to blacklist twitter users, open blacklist.txt (create it if you deleted it or it's missing) and add the user twitter handle (without the @) in the file.
One handle by line.
You can also put your own twitter handle in, so you don't try to join your own raids by mistake.

== JSON ==
The 'raid.json' file is used to load all raids displayed on the ui and more. You can edit it to add/remove raids or change the presentation.
Always backup your file when editing. Also, if you encounter errors, check you didn't forget a comma between two objects.

Quick explanation:
* "custom color" if the Custom tab background color
* A page correspond to a tab:
    * "name" is its name
    * "color" is its background color
    * "list" contains all the raids to be displayed in this tab
    * A raid in the "list" has 5 fields:
        * its "name"
        * its "english" and "japanese" codes
        * its position on the tab, "posX" being the horizontal position and "posY" the vertical one. Just imagine the tab is a 2D grid.

== SOUND FILE (for Windows) ==
Just replace 'alert.wav' with another file if you want to change the sound effect.
It must be named 'alert.wav'

== LINUX AND MAC ==
The installation should be similar.
I didn't test on linux and mac but the sound part shouldn't work because the winsound lib is only for windows.
I'm using beep for linux, install it with 'apt-get install beep' or whatever your install software is.
I have no solution for mac. Feel free to edit the script if you have one, though.

== TROUBLESHOOTING ==
You can rename 'gbfraidcopier.pyw' into 'gbfraidcopier.py' to open the command prompt. An error message may appear on this.
Alternatively on Windows, shift+right click in the folder > "Open a command prompt here" > type the command "python gbfraidcopier.pyw" without the quotes. If python isn't in your PATH, you need to write its full path instead of just "python".