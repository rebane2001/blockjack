# Blockjack

This is a simplified public version of my Discord bot for YouTube archive. While it is made specifically for the Omniarchive, anybody is welcome to use it for their own archival projects.

## Set up
1. Install python3 and dependencies (`pip3 install requests discord.py -U`).
2. Open up the `config.py` file and configure it how you please.
3. Fill out the secrets section of `config.py`, use the links included if you don't have the API keys.
4. Create the downloads file you specified (`download.txt` by default).
5. Run `blockjack.py`.

(optional) Set up some sort of a simple backup for your files, such as a git repository, in case something goes wrong or something.

## Usage
This bot will accept video and playlist links in the submissions channels. Previously added and duplicate video IDs will not be added. Discord channel IDs can also be added to the filtering sections in the config file to save only unlisted or pre-2017 videos based on the channel.

 - The download file will be filled with youtube links of submitted video IDs (video IDs will be extracted from playlists).
 - The submissions log file will keep a log of what new IDs who submitted, it can be turned off by disabling the "log_submissions" option.
 - The playlists log file will keep data for every playlist every time it is submitted, just in case.

Note that Blockjack will **not** download videos - it simply creates the list of links you can use with a program such as youtube-dl.

![1186722.png](https://derpicdn.net/img/2016/6/25/1186722/small.png)