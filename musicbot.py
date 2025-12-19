import discord
from discord.ext import commands 
import yt_dlp
import asyncio
import re

#  Bot setup

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!",
intents=intents)

# FFmpeg Options 
FFMPEG_OPTIONS = {
    'before_options' : '-reconnect 1 -reconnect_streamed 1 -reconnect_delay__max5',
    'options': '-vn'
}
 
 # Music Queues 
guild_queues = {}

#  Helper Functions

def get_youtube_url(query):
    """
    Search Youtube using yt-d1p and return first video URL
     Works fir song names or Spotify URLs 

     """
    # If its already a Youtube URL, return it
    youtube_regex = r"(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+"
    if re.match(youtube_regex, query):
        return query
    
    # ELSE SEARCH ON YOUTUBE 
    ydl_opts = {'format': 'bestaudio', 'noplaylist': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)['entries'][0]
            return info['webpage_url']
        except Exception:
            return None
def play_next(ctx):
    """Play the next song in the queue"""
    if guild_queues.get(ctx.guild.id):
        next_url = guild_queues[ctx.guild.id].pop(0)
        ctx.voice_client.play(discord.FFmpegPCMAudio(next_url, **FFMPEG_OPTIONS),
                              after=lambda e: play_next(ctx))
    else:
        coro = ctx.voice_client.disconnect()
        asyncio.run_coroutine_threadsafe(coro, bot.loop)

#   BOt Commands 
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await channel.connect()
        else:
            await ctx.voice_client.move_to(channel)
        await ctx.send(f"Joined {channel}")
    else:
        await ctx.send("You are not in a voice channel!")

@bot.command ()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Disconnected from voice channel!")
    else:
        await ctx.send("I am not in a voice channel!")

@bot.command()
async def play(ctx, *, query):
    if ctx.voice_client is None:
        await ctx.invoke(join)

    url = get_youtube_url(query)
    if url is None:
        await ctx.send("Could not find the song on YouTube!")
        return

    if ctx.guild.id in guild_queues:
        guild_queues[ctx.guild.id].append(url)
        await ctx.send(f"Added to queue: {query}")
    else:
        guild_queues[ctx.guild.id] = []
        ctx.voice_client.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS),
                              after=lambda e: play_next(ctx))
        embed = discord.Embed(title="Now Playing", description=query, color=discord.Color.green())
        await ctx.send(embed=embed)

@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Paused ⏸️")

@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("Resumed ▶️")
@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Skipped ⏭️")
    else:
        await ctx.send("Nothing is playing!")

@bot.command()
async def queue(ctx):
    if ctx.guild.id not in guild_queues or len(guild_queues[ctx.guild.id]) == 0:
        await ctx.send("Queue is empty!")
        return
    msg = "**Upcoming Songs In your vibe:**\n"
    for i, song in enumerate(guild_queues[ctx.guild.id], 1):
        msg += f"{i}. {song}\n"
    await ctx.send(msg)

@bot.command()
async def np(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        await ctx.send(f"Now Playing: {ctx.voice_client.source.url}")
    else:
        await ctx.send("Nothing is playing!")

# ---------- Run Bot ----------
bot.run("YOUR_BOT_TOKEN")


        
