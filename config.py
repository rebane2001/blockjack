# Prevent downloading unwanted videos in specific channels
filtering = {
    "unlisted_only": ["123456789012345678"],
    "pre2017_only":  ["123456789012345678"],
}

discord = {
    # The channel IDs for Discord channels people will be submitting videos in
    "submit_channels": ["123456789012345678"],
    "log_submissions": True,
    # Emojis are either literally the emoji (⏳) or the square bracket thing (<:blackjack:852661559829856276>)
    "emoji": {
        "already_added": "✅",
        "done": "🚀",
        "wait": "⏳",
        "fail": "❌",
    }
}

# Enable or disable logging of playlist and videos API data
logging = {
    "playlists": True,
    "videos": True,
}

# By default, paths are relative to where you run the script from. Absolute paths can be used if desired.
paths = {
    # Lists of video ids you wish to avoid downloading, can have multiple files
    "existing": ["download.txt"],
    # Submitted IDs will be added here as unified format youtube urls (https://www.youtube.com/watch?v=XXXXXXXXXXX), one per line
    "download": "download.txt",
    # Dumps playlist data just in case
    "playlist_log": "playlist_log.jsonl",
    # Dumps video data just in case
    "video_log": "video_log.jsonl",
    # Additional useful data about user submissions will be logged here
    "submissions_log": "submissions.jsonl",
}

# Don't give these out to anyone, they're called secrets for a reason
secrets = {
    # Get your key: https://discord.com/developers/applications
    "discord_api_key": "DISCORD_BOT_API_KEY",
    # Get your key: https://console.cloud.google.com/apis/credentials
    "youtube_api_key": "YOUTUBE_API_KEY",
}