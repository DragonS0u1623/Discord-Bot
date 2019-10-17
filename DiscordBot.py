from os import system
import os
import shutil

import discord
from discord.utils import get
from pymongo import MongoClient
import youtube_dl

from discord.ext import commands


TOKEN

global client
global voice
client = MongoClient("mongodb+srv://<username>:<password>@discord-y3bzo.mongodb.net/test?retryWrites=true&w=majority")
db = client["bot"]
server_coll = db["serversettings"]
queue_coll = db["queues"]

#TODO: Mongodb queues 

def get_prefix(bot, message):
    if not message.guild:
        return commands.when_mentioned_or("?")(bot, message)
    prefix = "?"
    for x in server_coll.find({"guildid": message.guild.id}, {"_id": 0}):
        prefix = x["prefix"]
        return commands.when_mentioned_or(prefix)(bot, message)

bot = commands.Bot(command_prefix=get_prefix, case_insensitive=True)
bot.remove_command("help")

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

@bot.event
async def on_guild_join(guild):
    post = {"guildid": guild.id, "money": 0, "voice channel": 0, "prefix": "?"}
    server_coll.insert_one(post)
    print("Created document for " + guild.name + ": " + str(guild.id))

@bot.event
async def on_guild_remove(guild):
    post = {"guildid": guild.id}
    server_coll.delete_one(post)
    print("Deleted document for " + guild.name + ": " + str(guild.id))

@bot.event
async def on_member_join(member):
    embed = discord.Embed(colour=discord.Colour.orange(), title=f"Member joined: {member}", description="Joined the server.")
    await auditChannel.send(embed)

@bot.event 
async def on_member_remove(member):
    embed = discord.Embed(colour=discord.Colour.orange(), title=f"Member left: {member}", description="Left the server.")
    await auditChannel.send(embed)

@bot.command()
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

@bot.command()
async def prefix(ctx, message):
    mq = {'guildid': ctx.guild.id}
    change = {'$set': {'prefix': message}}
    server_coll.update_one(mq, change)
    print('Prefix changed to ' + message + ' for ' + ctx.guild.name + ': ' + str(ctx.guild.id))
    await ctx.send('Prefix changed to ' + message)

@bot.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')
    
@bot.command()
async def clear(ctx, amount=25):
    manageChannels = False
    for role in ctx.author.roles:
        if role.permissions.manage_channels:
            manageChannels = True
            break
    if manageChannels:
        await ctx.channel.purge(limit=amount+1)
        print(f'Cleared {amount} messages from {ctx.channel}')
    else:
        await ctx.send("You don't have permission to use this command.")

@bot.command()
async def channel(ctx, channel : discord.TextChannel):
    admin = False
    for role in ctx.author.roles:
        if role.permissions.administrator:
            admin = True
            break
    if admin:
        global auditChannel 
        auditChannel = channel
        await ctx.send(f"Audit log data will be sent to {auditChannel}")
    else:
        await ctx.send("You don't have permission to use this command.")

@bot.command()
async def kick(ctx, member : discord.Member, *, reason=None):
    canKick = False
    for role in ctx.author.roles:
        if role.permissions.kick_members:
            canKick = True
            break
    if canKick:
        embed = discord.Embed(colour=discord.Colour.orange(), title=f"Member Kicked: {member}", description="Removed from the server.")
        embed.add_field(name="Reason: " + reason, inline=False)
        embed.add_field(name=f"Responsible operator: {ctx.author.mention}", inline=False)
        await member.kick(reason=reason)
        await auditChannel.send(embed)
    else:
        await ctx.send("You don't have permission to use this command.")

@bot.command()
async def ban(ctx, member : discord.Member, *, reason=None):
    canBan = False
    for role in ctx.author.roles:
        if role.permissions.ban_members:
            canBan = True
            break
    if canBan:
        embed = discord.Embed(colour=discord.Colour.orange(), title=f"Member banned: {member}", description="Banned from the server.")
        embed.add_field(name="Reason: " + reason, inline=False)
        embed.add_field(name=f"Responsible operator: {ctx.author.mention}", inline=False)
        await member.ban(reason=reason)
        await auditChannel.send(embed)
    else:
        await ctx.send("You don't have permission to use this command.")

@bot.command()
async def unban(ctx, member : discord.Member, *, reason=None):
    canBan = False
    for role in ctx.author.roles:
        if role.permissions.ban_members:
            canBan = True
            break
    if canBan:
        embed = discord.Embed(colour=discord.Colour.orange(), title=f"Member unbanned: {member}", description="Unbanned from the server.")
        embed.add_field(name="Reason: " + reason, inline=False)
        embed.add_field(name=f"Responsible operator: {ctx.author.mention}", inline=False)
        await member.unban(reason=reason)
        await auditChannel.send(embed)
    else:
        await ctx.send("You don't have permission to use this command.")

@bot.command(aliases=['j'])
async def join(ctx):
    channel = ctx.author.voice.channel
    voice = get(bot.voice_clients, guild=ctx.guild)
    
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()
        print(f'The bot has connnected to {channel}\n')
        await ctx.send(f'Connected to {channel}')

@bot.command(aliases=['l'])
async def leave(ctx):
    channel = ctx.author.voice.channel
    voice = get(bot.voice_clients, guild=ctx.guild)
    
    if voice and voice.is_connected():
        await voice.disconnect()
        await ctx.send(f'Left {channel}')
    else:
        print("Don't think I can do that chief. Doesn't look like I'm in a voice channel.")
        await ctx.send("Don't think I can do that chief. Doesn't look like I'm in a voice channel.")

@bot.command(aliases=['p'])
async def play(ctx, url: str):
    
    def check_queue():
        queue_infile = os.path.isdir('./Queue')
        if queue_infile is True:
            DIR = os.path.abspath(os.path.realpath('Queue'))
            length = len(que)
            still_q = length - 1
            search = queue_coll.find_one({'guildid': ctx.guild.id, 'song_num': 1})
            dwnld = search['url']
            q_num = search['song_num']
            queue_path = os.path.abspath(os.path.realpath("Queue"))
            print("Downloading song to: " + queue_path)
            ydl_opts = {
                'format': 'bestaudio/best',
                'noplaylist': '',
                'default_search': 'ytsearch',
                'outtmpl': queue_path,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                    }],
                }
            try:
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    print("Downloading Queued audio now\n")
                    ydl.download([dwnld])
            except:
                print("FALLBACK: Youtube-dl does not support this URL, using Spotify (This is normal if Spotify URL)")
                system("spotdl -f " + '"' + queue_path + '" -nf ' + " -s " + dwnld)
            
            print('Song downloaded.')
            queue_coll.delete_one({'guildid': ctx.guild.id, 'song_num': 1})
            
            for x in queue_coll.find({'guildid': ctx.guild.id}):
                    num = x["song_num"]
                    queue_coll.update_one(x, {'$set': {'song_num': (num-1)}})
            print("Collection updated")
            try:
                first_file = os.listdir(DIR)[0]
                print("Found first file")
            except:
                print('No more songs queued\n')
                que.clear()
                queue_coll.delete_many({'guildid': ctx.guild.id})
                print("Collection cleared")
                return 
            main_location = os.path.dirname(os.path.realpath(__file__))
            song_path = os.path.abspath(os.path.realpath('Queue') + "\\" + first_file)
            print("Found file path")
            if length != 0:
                print('Song done. Playing next in Queue\n')
                print(f'Songs still in queue: {still_q}')
                song_there = os.path.isfile('song.mp3')
                if song_there:
                    os.remove('song.mp3')
                    shutil.move(song_path, main_location)
                    print("Removed old song file")
                for file in os.listdir('./'):
                    if file.endswith('.mp3'):
                        os.renames(file, 'song.mp3')
                        print("Renamed new song to song.mp3")
                        
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

    voice = get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()
        await ctx.send(f'Connected to {channel}')
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': '',
        'default_search': 'ytsearch',
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
        system("spotdl -f " + '"' + c_path + '" -nf ' + " -s " + url)

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
    
@bot.command(aliases=[])
async def pause(ctx):
    voice = get(bot.voice_clients, guild=ctx.guild)
    
    if voice and voice.is_playing():
        print("Music paused")
        voice.pause()
        await ctx.send("Music paused")
    else:
        print("Nothing is playing chief")
        await ctx.send("Nothing is playing chief")
    
@bot.command(aliases=['r'])
async def resume(ctx):
    voice = get(bot.voice_clients, guild=ctx.guild)
    
    if voice and voice.is_paused():
        print("Music resumed")
        voice.resume()
        await ctx.send("Music resumed")
    else:
        print("Music is already playing chief")
        await ctx.send("Music is already playing chief")
        
    
@bot.command(aliases=['s'])
async def stop(ctx):
    voice = get(bot.voice_clients, guild=ctx.guild)
    que.clear()
    
    queue_infile = os.path.isdir("./Queue")
    if queue_infile is True:
        shutil.rmtree('./Queue')
    queue_coll.delete_many({'guildid': ctx.guild.id})
    print("Music stopped")
    voice.stop()
    await ctx.send("Music stopped")

que = {}

@bot.command(aliases=['q'])
async def queue(ctx, url: str):
    queue_infile = os.path.isdir("./Queue")
    if queue_infile is False:
        os.mkdir("Queue")
    q_num = len(que)
    q_num += 1
    add_queue = True
    while add_queue:
        if q_num in que:
            q_num += 1
        else:
            add_queue = False
            que[q_num] = q_num
    queue_coll.insert_one({'guildid': ctx.guild.id, 'song_num': q_num, 'url': url})
    await ctx.send("Adding song " + str(q_num) + " to the queue")

@bot.command(aliases=['n', 'next'])
async def _next(ctx):
    voice = get(bot.voice_clients, guild=ctx.guild)
    print("Playing next song")
    voice.stop()
    await ctx.send("Playing next song")

bot.run(TOKEN)