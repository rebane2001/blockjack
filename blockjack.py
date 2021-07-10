#!/usr/bin/env python3
import requests
import re
import discord
import os
import time
import json
from datetime import datetime, timezone

import config

client = discord.Client()

def getLinkType(link):
    if re.search(r'((c|channel|user)/[^?/]+)', link):
        return 0
    if re.search(r'/watch\?v=([A-Za-z0-9_\-]{11})', link):
        return 1
    if re.search(r'/watch\?.*?&v=([A-Za-z0-9_\-]{11})', link):
        return 1
    if re.search(r'youtu.be/([A-Za-z0-9_\-]{11})', link):
        return 1
    if re.search(r'/shorts/([A-Za-z0-9_\-]{11})', link):
        return 1
    if re.search(r'/embed/([A-Za-z0-9_\-]{11})', link):
        return 1
    if re.search(r'/playlist\?list=([A-Za-z0-9_\-]{16,64})', link):
        return 2
    if re.search(r'/playlist\?.*&list=([A-Za-z0-9_\-]{16,64})', link):
        return 2
    return -1

def extractPlaylist(link):
    vidmatch = re.search(r'/playlist\?list=([A-Za-z0-9_\-]{16,64})', link)
    if vidmatch:
        return vidmatch.group(1)
    vidmatch = re.search(r'/playlist\?.*?&list=([A-Za-z0-9_\-]{16,64})', link)
    if vidmatch:
        return vidmatch.group(1)
    return "ERROR EXTRACTING VID: " + link

def extractPlaylists(link):
    matches = []
    vidmatch = re.findall(r'/playlist\?list=([A-Za-z0-9_\-]{16,64})', link)
    if vidmatch:
        matches.extend(vidmatch)
    vidmatch = re.findall(r'/playlist\?.*?&list=([A-Za-z0-9_\-]{16,64})', link)
    if vidmatch:
        matches.extend(vidmatch)
    return matches

def extractVids(link):
    matches = []
    vidmatch = re.findall(r'/watch\?v=([A-Za-z0-9_\-]{11})', link)
    if vidmatch:
        matches.extend(vidmatch)
    vidmatch = re.findall(r'&v=([A-Za-z0-9_\-]{11})', link)
    if vidmatch:
        matches.extend(vidmatch)
    vidmatch = re.findall(r'youtu.be/([A-Za-z0-9_\-]{11})', link)
    if vidmatch:
        matches.extend(vidmatch)
    vidmatch = re.findall(r'/shorts/([A-Za-z0-9_\-]{11})', link)
    if vidmatch:
        matches.extend(vidmatch)
    vidmatch = re.findall(r'/embed/([A-Za-z0-9_\-]{11})', link)
    if vidmatch:
        matches.extend(vidmatch)
    return matches

def getEmoji(emoji):
    return config.discord['emoji'][emoji]

allids = set()

def updateIDs():
    global allids
    allids = set()
    for file in config.paths["existing"]:
        with open(f"{file}", "r", encoding="UTF-8") as f:
            for l in f:
                # Strip unnecessary parts and leave only the video ID
                videoid = l.replace("https://www.youtube.com/watch?v=", "").replace("youtube ", "").strip()
                allids.add(videoid)

def videoAlreadyAdded(videoid):
    return videoid in allids

# Some snippets borrowed from https://github.com/itallreturnstonothing/panicpony/
def get_playlists_page(playlist_id, page_token=None):
    response = requests.get(
            (
                f'https://www.googleapis.com/youtube/v3/playlistItems?'
                f'playlistId={playlist_id}'
                f'&part=status,snippet,contentDetails'
                f'&maxResults=50'
                f'{"&pageToken=" + page_token if page_token else ""}'
                f'&key={config.secrets["youtube_api_key"]}'
            )
        )

    if not response.status_code == 200:
        print("Something not right!")
        return ([], None)

    precious_data = json.loads(response.text)
    return (
                precious_data["items"],
                precious_data["nextPageToken"] if "nextPageToken" in precious_data else None
            )

def get_videos_page(video_ids):
    response = requests.get(
            (
                f'https://www.googleapis.com/youtube/v3/videos?'
                f'id={",".join(video_ids)}'
                f'&part=status,snippet,contentDetails'
                f'&maxResults=50'
                f'&key={config.secrets["youtube_api_key"]}'
            )
        )

    if not response.status_code == 200:
        print("Something not right!")
        return ([], None)

    precious_data = json.loads(response.text)
    return precious_data["items"]

pl_page = 0
def get_all_videos_from_playlist(playlist_id):
    global pl_page
    pl_page = 1
    print("Fetching playlist")
    (first_videos, next_page) = get_playlists_page(playlist_id)
    def amazing(next_page):
        global pl_page
        while next_page:
            pl_page+=1
            print(f"Fetching playlist (page {pl_page}, {pl_page*50} videos)")
            next_videos, next_page = get_playlists_page(playlist_id,next_page)
            yield next_videos

    return [x for flatten_list in [first_videos] + list(amazing(next_page)) for x in flatten_list]

def get_all_videos_from_ids(video_ids):
    print("Fetching videos")
    data = []
    while len(video_ids) > 0:
        data += get_videos_page(video_ids[:50])
        video_ids = video_ids[50:]
    return data

def parse_date_format(date_str):
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

def log_message(message,logtype):
    event = {
        "user": str(message.author),
        "userid": message.author.id,
        "message": message.content,
        "message_id": message.id,
        "created_at": message.created_at.timestamp(),
        "timestamp": time.time(),
    }
    with open(config.paths[logtype], "a", encoding="UTF-8") as f:
        f.write(f"{json.dumps(event)}\n")

async def splitReply(message, reply):
    remaining = reply
    while len(remaining) > 0:
        await message.reply(remaining[:1950])
        remaining = remaining[1950:]

async def processVideoList(message, video_ids_orig):
    # Dedupe
    video_ids = list(dict.fromkeys(video_ids_orig))
    report = ""
    # Do not report already added videos if many videos are submitted
    report_dupe = len(video_ids) < 40
    dupe_count = 0
    new_ids = []
    updateIDs()
    print(f"Processing {len(video_ids)} videos...")
    for video_id in video_ids:
        if videoAlreadyAdded(video_id):
            if len(video_ids) == 1:
                await message.reply("Video already added!")
                await message.add_reaction(getEmoji('already_added'))
            else:
                if report_dupe:
                    report += f"{getEmoji('already_added')} {video_id} already added!\n"
                else:
                    dupe_count += 1
        else:
            if len(video_ids) == 1:
                await message.add_reaction(getEmoji('done'))
            else:
                report += f"{getEmoji('done')} {video_id} added!\n"
            new_ids.append(video_id)
            with open(config.paths["download"], "a", encoding="UTF-8") as f:
                f.write(f"https://www.youtube.com/watch?v={video_id}\n")
    await message.clear_reaction(getEmoji('wait'))
    print(f"Processed!")
    if len(report) > 0 or dupe_count > 0:
        await message.add_reaction(getEmoji('done'))
        if len(report) > 1900:
            report = report.replace(" already added!","").replace(" added!","")
        if dupe_count > 0 and not report_dupe:
            report = f"__{getEmoji('already_added')} **{dupe_count} videos already added!**__\n{report}"
        await splitReply(message, report)
    # Log which new ids were submitted and by whom
    if len(new_ids) > 0 and config.discord['log_submissions']:
        event = {
            "user": str(message.author),
            "userid": message.author.id,
            "message": message.content,
            "new_ids": new_ids,
            "message_id": message.id,
            "created_at": message.created_at.timestamp(),
            "timestamp": time.time(),
        }
        with open(config.paths["submissions_log"], "a", encoding="UTF-8") as f:
            f.write(f"{json.dumps(event)}\n")

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    # Ignore messages from myself
    if message.author == client.user:
        return

    # Submit channel message received
    if str(message.channel.id) in config.discord['submit_channels']: 
        if config.discord['log_all']:
            log_message(message,"all_messages_log")
        if "logout" in message.content.lower():
            await message.reply("bruh")
            await message.add_reaction('🤨')
        if not ("youtube." in message.content or "youtu.be" in message.content):
            if config.discord['log_missed']:
                log_message(message,"missed_messages_log")
            return
        unlisted_only = str(message.channel.id) in config.filtering['unlisted_only']
        pre2017_only = str(message.channel.id) in config.filtering['pre2017_only']
        await message.add_reaction(getEmoji('wait'))
        linktype = getLinkType(message.content)
        if linktype == -1:
            await message.clear_reaction(getEmoji('wait'))
            await message.add_reaction(getEmoji('fail'))
            await message.reply("That doesn't seem like a proper YouTube link.")
            if config.discord['log_missed']:
                log_message(message,"missed_messages_log")
        elif linktype == 0:
            await message.clear_reaction(getEmoji('wait'))
            await message.add_reaction(getEmoji('fail'))
            await message.reply("Adding channels is not enabled.")
            if config.discord['log_missed']:
                log_message(message,"missed_messages_log")
        elif linktype > 0:
            if linktype == 1:
                video_ids = extractVids(message.content)
                videos = get_all_videos_from_ids(video_ids)
                if config.logging['videos']:
                    with open(config.paths["video_log"], "a", encoding="UTF-8") as f:
                        for video in videos:
                            f.write(f"{json.dumps(video)}\n")
            elif linktype == 2:
                playlist_ids = extractPlaylists(message.content)
                if len(playlist_ids) > 1 and not config.discord['multiple_playlists']:
                    playlist_ids = [playlist_ids[0]]
                    await message.reply("Warning! Only one playlist per message will be processed.")
                    if config.discord['log_missed']:
                        log_message(message,"missed_messages_log")
                videos = []
                for playlist_id in playlist_ids:
                    playlist_videos = get_all_videos_from_playlist(playlist_id)
                    videos += playlist_videos
                    if config.logging['playlists']:
                        with open(config.paths["playlist_log"], "a", encoding="UTF-8") as f:
                            f.write(f"{json.dumps(playlist_videos)}\n")
                if config.logging['videos']:
                    with open(config.paths["video_log"], "a", encoding="UTF-8") as f:
                        for video in videos:
                            f.write(f"{json.dumps(video)}\n")
            orig_len = len(videos)
            print(f"Got {len(videos)} videos")
            if unlisted_only or pre2017_only:
                critical_datetime = datetime(year=2017, month=1, day=2, tzinfo=timezone.utc)
                videos = list(filter(lambda x: x["status"]["privacyStatus"] == "unlisted", videos))
                if pre2017_only:
                    videos = [(x, parse_date_format(x["contentDetails"]["videoPublishedAt"] if linktype == 2 else x["snippet"]["publishedAt"])) for x in videos]
                    videos = list(filter(lambda x: x[1] < critical_datetime, videos))
                    videos = [x[0] for x in videos]
                print(f"Filtered down to {len(videos)} videos")
                if len(videos) == 0:
                    await message.clear_reaction(getEmoji('wait'))
                    await message.add_reaction('🤔')
                    await message.reply("No videos to process found!")
                    return
                await message.reply(f"Processing {len(videos)} out of {orig_len} videos{' in the playlist' if linktype == 2 else ''}")
            video_ids = [vid["snippet"]["resourceId"]["videoId"] if linktype == 2 else vid["id"] for vid in videos]
            await processVideoList(message, video_ids)

print("Starting up...")
client.run(config.secrets["discord_api_key"])
