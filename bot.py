# This example requires the 'message_content' intent.

import discord
import asyncio
import random
import requests
import shutil
import mimetypes
import os
import uuid

from PIL import Image
from pathlib import Path
from time import sleep

from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# async def send_image():

@bot.command()
async def response(ctx):
    print("test command")
    await ctx.send(channel)

@bot.command()
async def image(ctx):
    print("image command")
    await ctx.send(file=discord.File('test.png'))

@bot.command()
async def magik(ctx, arg1=None):
    workid = str(uuid.uuid4())
    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}
    req = None
    found = 0
    download = 0
    attempt = 0


    video = 0
    audio = 0

    if arg1 == "vid":
        audio = 1

    image = 0
    size = 0

    filetype = None
    randheight = random.randrange(50,150)
    randwidth = random.randrange(50,150)
    randblur = random.randrange(50,250)


    withattachments = []
    channel = ctx.channel

    if ctx.message.reference is not None:
        print("This is a reply")
        message = await channel.fetch_message(ctx.message.reference.message_id)
        print(message)
    else:
        async for message in channel.history(limit=5):
            if message.attachments or message.embeds:
                withattachments.append(message.id)
        id = withattachments[0]
        print(id)
        message = await channel.fetch_message(id)
        print(message)

    if message.attachments:
        await message.attachments[0].save(f"{workid}")
        download = 1
        filetype = str(message.attachments[0].content_type)
        print(filetype)
        match filetype:
            case "image/gif":
                video = 1
            case "video/mp4":
                video = 1
            case "video/quicktime":
                video = 1
    elif message.embeds:
        print(message.embeds[0].url)
        print(message.embeds[0].image)
        print(message.embeds[0].thumbnail)
        print(message.embeds[0].provider)
        print(message.embeds[0].video.proxy_url)
        print(message.embeds[0].image.proxy_url)
        print(message.embeds[0].image.url)
        print(message.embeds[0].image.flags)
        print(message.embeds[0].url)

        while found == 0:
            sleep(1)
            req = None
            match attempt:
                case 0:
                    if message.embeds[0].url != None:
                        req = requests.get(str(message.embeds[0].url), headers=hdr)
                case 1:
                    if message.embeds[0].video.proxy_url != None:
                        req = requests.get(str(message.embeds[0].video.proxy_url), headers=hdr)
                case 2:
                    if message.embeds[0].image.proxy_url != None:
                        req = requests.get(str(message.embeds[0].image.proxy_url), headers=hdr)
                case 3:
                    if message.embeds[0].thumbnail.proxy_url != None:
                        req = requests.get(str(message.embeds[0].thumbnail.proxy_url), headers=hdr)
                case 10:
                    break

            if req == None:
                print(f"Seems like attempt {attempt} failed, trying alternatives")
                attempt += 1
                continue
            elif "<!DOCTYPE html>" in str(req.content):
                print(f"Webpage was downloaded, trying alternatives (attempt {attempt})")
                attempt += 1
                continue
            elif "404" in str(req.status_code):
                print(f"404'd on URL, trying alternatives (attempt {attempt})")
                attempt += 1
                continue
            elif "video" in str(req.headers.get('Content-Type')):
                print("found video")
                filetype = str(mimetypes.guess_extension(req.headers.get('Content-Type')))
                video = 1
                found = 1
            elif "gif" in str(req.headers.get('Content-Type')):
                print("found gif")
                filetype = str(mimetypes.guess_extension(req.headers.get('Content-Type')))
                video = 1
                found = 1
            else:
                print(f"attempt {attempt} failed, moving on")
                attempt += 1
                video = 0

    if video == 1:
        if download == 0:
            if req is not None:
                with open(f"{workid}", 'wb') as f:
                    for chunk in req.iter_content(1024):
                        f.write(chunk)

        os.mkdir(f"./{workid}-folder")

        #Get framerate
        frame = await asyncio.create_subprocess_shell(f'ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of default=noprint_wrappers=1:nokey=1 {workid}', stdout=asyncio.subprocess.PIPE)
        framerate = await frame.communicate()
        print(framerate)
        framerate = framerate[0].decode('ascii')
        framerate = framerate.strip()
        print(framerate)

        #split input into series of pngs
        splitproc = await asyncio.create_subprocess_shell(f'ffmpeg -hide_banner -loglevel error -i {workid} -fps_mode passthrough ./{workid}-folder/frame%04d.png', stdout=asyncio.subprocess.PIPE)
        split = await splitproc.communicate()

        #Gather the dimensions of a single frame for max wackiness on the resizing
        with Image.open(f"./{workid}-folder/frame0001.png") as image:
            width, height = image.size

        #Calc some decent values to use randomly
        maxheightwiggle = round(height/2)
        maxwidthwiggle = round(width/2)

        minheightwiggle = round(height/3)
        minwidthwiggle = round(width/3)

        #Run mogrify in parallel for speed, wiggling variably with the math from earlier
        liquid = await asyncio.create_subprocess_shell(f'cd ./{workid}-folder; ls *.png | parallel mogrify -liquid-rescale {width - random.randrange(minwidthwiggle,maxwidthwiggle)}x{height - random.randrange(minheightwiggle,maxheightwiggle)} {{}}', stdout=asyncio.subprocess.PIPE)
        stdout, stderr = await liquid.communicate()

        if audio == 0:
            print("making a gif")
            #Generate a gif based on the mass png modifications
            gifproc = await asyncio.create_subprocess_shell(f'ffmpeg -hide_banner -loglevel error -framerate {framerate} -i ./{workid}-folder/frame%04d.png {workid}.gif -y', stdout=asyncio.subprocess.PIPE)
            gif = await gifproc.communicate()

            #Check if we're over the max size for an upload on discord
            size = os.path.getsize(f'{workid}.gif')

            #Make a mini-gif in 480p as an attempt to salvage a massive file
            if size >= 20000000:
                gifresizeproc = await asyncio.create_subprocess_shell(f'ffmpeg -y -i "{workid}.gif" -filter_complex "fps=20,scale=480:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=32[p];[s1][p]paletteuse=dither=bayer" -loop 0 {workid}-mini.gif', stdout=asyncio.subprocess.PIPE)
                gifresize = await gifresizeproc.communicate()
                os.remove(f'{workid}.gif')
                os.replace(f'{workid}-mini.gif',f'{workid}.gif')

            #Send it!
            await ctx.send(file=discord.File(f'{workid}.gif'))

            #Clean up all the scratch used in generation
            shutil.rmtree(f"./{workid}-folder")
            os.remove(f"{workid}.gif")
            os.remove(f"{workid}")

        if audio == 1:
            print("making a video")
            audioproc = await asyncio.create_subprocess_shell(f'ffmpeg -hide_banner -loglevel error -i ./{workid} -map 0:a -c copy {workid}-audio.mov -y', stdout=asyncio.subprocess.PIPE)
            audio = await audioproc.communicate()

            vidproc = await asyncio.create_subprocess_shell(f'ffmpeg -hide_banner -loglevel error -framerate {framerate} -i ./{workid}-folder/frame%04d.png -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -c:v libsvtav1 {workid}-video.mp4 -y', stdout=asyncio.subprocess.PIPE)
            vid = await vidproc.communicate()

            shuffleproc = await asyncio.create_subprocess_shell(f'ffmpeg -hide_banner -loglevel error -i {workid}-video.mp4 -i {workid}-audio.mov -c copy -map 0:v:0 -map 1:a:0 {workid}.mp4 -y', stdout=asyncio.subprocess.PIPE)
            suffle = await shuffleproc.communicate()

            #Send it!
            await ctx.send(file=discord.File(f'{workid}.mp4'))

            #Clean up all the scratch used in generation
            shutil.rmtree(f"./{workid}-folder")
            os.remove(f"{workid}.mp4")
            os.remove(f"{workid}-video.mp4")
            os.remove(f"{workid}-audio.mov")
            os.remove(f"{workid}")





bot.run('')

