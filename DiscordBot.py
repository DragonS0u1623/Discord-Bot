from os import system
import os
import shutil

import discord
from discord.utils import get
import youtube_dl

from discord.ext import commands

#TODO:Youtube search 
#TODO: Mongodb queues 
#TODO: Multi server compatibility with mongodb

PREFIX = '.'

client = commands.Bot(command_prefix=PREFIX)

client.remove_command("help")

@client.command()
async def help(ctx):
    author = ctx.message.author
    
    embed = discord.Embed(colour=discord.Colour.red(), title="Discord Music Bot Commands", description="All commands of this bot.")
    embed.add_field(name="ping", value="Makes the bot say Pong and gives latency", inline=False)
    embed.add_field(name="join", value="Makes the bot join your current voice channel", inline=False)
    embed.add_field(name="leave", value="Makes the bot leave your current voice channel", inline=False)
    embed.add_field(name="play", value="Makes the bot play music in your current voice channel", inline=False)
    embed.add_field(name="pause", value="Makes the bot pause currently playing music", inline=False)
    embed.add_field(name="next", value="Makes the bot skip to the next song", inline=False)
    embed.add_field(name="stop", value="Makes the bot stop playing music", inline=False)
    embed.add_field(name="resume", value="Makes the bot resume paused music", inline=False)
    embed.add_field(name="queue", value="Makes the bot queue a new song to play next", inline=False)
    
    await author.send(embed=embed)

@client.event 
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.command()
async def prefix(ctx, message):
    PREFIX = message
    print('Prefix changed to ' + PREFIX + ' for ' + ctx.author.server)
    await ctx.send('Prefix changed to ' + PREFIX)

@client.command()
async def ping(ctx):
    print(f'Pong! {round(client.latency * 1000)}ms')
    await ctx.send(f'Pong! {round(client.latency * 1000)}ms')
    
@client.command(aliases=['j'])
async def join(ctx):
    global voice
    channel = ctx.author.voice.channel
    voice = get(client.voice_clients, guild=ctx.guild)
    
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()
        print(f'The bot has connnected to {channel}\n')
    
    await ctx.send(f'Connected to {channel}')

@client.command(aliases=['l'])
async def leave(ctx):
    channel = ctx.author.voice.channel
    voice = get(client.voice_clients, guild=ctx.guild)
    
    if voice and voice.is_connected():
        await voice.disconnect()
        await ctx.send(f'Left {channel}')
    else:
        print("Don't think I can do that chief. Doesn't look like I'm in a voice channel.")
        await ctx.send("Don't think I can do that chief. Doesn't look like I'm in a voice channel.")


@client.command(aliases=['p'])
async def play(ctx, url: str):
    
    def check_queue():
        queue_infile = os.path.isdir('./Queue')
        if queue_infile is True:
            DIR = os.path.abspath(os.path.realpath('Queue'))
            length = len(os.listdir(DIR))
            still_q = length - 1
            try:
                first_file = os.listdir(DIR)[0]
            except:
                print('No more songs queued\n')
                que.clear()
                return 
            main_location = os.path.dirname(os.path.realpath(__file__))
            song_path = os.path.abspath(os.path.realpath('Queue') + "\\" + first_file)
            
            if length != 0:
                print('Song done. Playing next in Queue\n')
                print(f'Songs still in queue: {still_q}')
                song_there = os.path.isfile('song.mp3')
                if song_there:
                    os.remove('song.mp3')
                    shutil.move(song_path, main_location)
                for file in os.listdir('./'):
                    if file.endswith('.mp3'):
                        os.renames(file, 'song.mp3')
                            
                voice.play(discord.FFmpegPCMAudio("song.mp3"), after=lambda e: check_queue())
                voice.source = discord.PCMVolumeTransformer(voice.source)
                voice.source.volume = 0.5
                    
            else:
                que.clear()
                print('No songs were queued before the end of the last song.\n')
    
    channel = ctx.author.voice.channel
    song_there = os.path.isfile("song.mp3")
    try:
        if song_there:
            os.remove("song.mp3")
            que.clear()
            print("Removed old song file")
    except PermissionError:
        print("Trying to delete song file, but it's being played")
        await ctx.send("ERROR: Music playing")
        return

    queue_infile = os.path.isdir('Queue')
    try:
        queue_folder = './Queue'
        if queue_infile is True:
            print('Removed old queue')
            shutil.rmtree(queue_folder)
    except:
        print('No old queue folder')
    
    await ctx.send("Getting everything ready now")

    voice = get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()
        await ctx.send(f'Connected to {channel}')
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            print("Downloading audio now\n")
            ydl.download([url])
            title = ydl.extract_info(url, download=False).get('title', None)
    except:
        print("FALLBACK: Youtube-dl does not support this URL, using Spotify (This is normal if Spotify URL)")
        c_path = os.path.dirname(os.path.realpath(__file__))
        system("spotdl -f " + '"' + c_path + '"' + " -s " + url)

    for file in os.listdir("./"):
        if file.endswith(".mp3"):
            name = file
            print(f'Renamed File: {file} to song.mp3\n')
            os.rename(file, "song.mp3")

    voice.play(discord.FFmpegPCMAudio("song.mp3"), after=lambda e: check_queue())
    voice.source = discord.PCMVolumeTransformer(voice.source)
    voice.source.volume = 0.5

    nname = name.rsplit("-", 2)
    try:
        await ctx.send(f'Playing: {nname[0]}\n')
        await ctx.send(f'Title: {title}\n')
    except:
        await ctx.send('Playing Song')
        
    print("playing\n")
    
@client.command(aliases=[])
async def pause(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    
    if voice and voice.is_playing():
        print("Music paused")
        voice.pause()
        await ctx.send("Music paused")
    else:
        print("Nothing is playing chief")
        await ctx.send("Nothing is playing chief")
    
@client.command(aliases=['r'])
async def resume(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    
    if voice and voice.is_paused():
        print("Music resumed")
        voice.resume()
        await ctx.send("Music resumed")
    else:
        print("Music is already playing chief")
        await ctx.send("Music is already playing chief")
        
que = {}
    
@client.command(aliases=['s'])
async def stop(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    que.clear()
    
    queue_infile = os.path.isdir("./Queue")
    if queue_infile is True:
        shutil.rmtree('./Queue')
    
    print("Music stopped")
    voice.stop()
    await ctx.send("Music stopped")

@client.command(aliases=['q'])
async def queue(ctx, url: str):
    queue_infile = os.path.isdir("./Queue")
    if queue_infile is False:
        os.mkdir("Queue")
    DIR = os.path.abspath(os.path.realpath("Queue"))
    q_num = len(os.listdir(DIR))
    q_num += 1
    add_queue = True
    while add_queue:
        if q_num in que:
            q_num += 1
        else:
            add_queue = False
            que[q_num] = q_num
    
    queue_path = os.path.abspath(os.path.realpath("Queue") + f'\song{q_num}.%(ext)s')
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': queue_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
            }],
        }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            print("Downloading audio now\n")
            ydl.download([url])
            await ctx.send("Adding song " + str(q_num) + " to the queue")
    except:
        print("FALLBACK: Youtube-dl does not support this URL, using Spotify (This is normal if Spotify URL)")
        q_path = os.path.abspath(os.path.realpath("Queue"))
        system(f'spotdl -ff song{q_num} -f ' + '"' + q_path + '"' + ' -s ' + url)
        print("Song added to queue")

@client.command(aliases=['n', 'next'])
async def _next(ctx):
    print("Playing next song")
    voice.stop()
    await ctx.send("Playing next song")

client.run('NjI5NDk0MTI2NzQzNjUwMzM2.XZlMiw.ITh_9N1nqTwrA99Tpf0---GWnQA')