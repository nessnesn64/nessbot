# This example requires the 'message_content' intent.

import discord
import asyncio
import random
import requests
import shutil
import mimetypes
import os
import uuid

from PIL import Image, ImageSequence
from pathlib import Path
from time import sleep

from discord.ext import commands, tasks

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents)

intents = discord.Intents.default()
intents.message_content = True

scratchmessage = []


client = discord.Client(intents=intents)

#Function to determine if a webp is a video or image. Fuck you Google.
async def IsAGif(workid):
    try:
        MediaFile = Image.open(f'{workid}')
        Index = 0
        for Frame in ImageSequence.Iterator(MediaFile):
            Index += 1
        if Index > 1: #Must mean the the .webp is a gif because it has more than one frame
            return True
        else: #Must mean that the .webp has 1 frame which makes it a image
            return False
    except: #If the .webp can't be opened then it is most likely not a .gif or .webp
        return None

#General function for gathering media from embeds or attachments.
async def getmedia(ctx, workid):

    #Create a header to spoof firefox to help with pesky downloads that block python requests
    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

    #Get the channel details with the passed context
    channel = ctx.channel

    #Set an null array for attachments in the last 5 messages
    withattachments = []

    #Set a variable to determine between video/image. 1 = Video, 2 = Image
    workingtype = None

    #Set found = 0 to allow for searching embeds
    found = 0

    attempt = 0

    filetype = None
    animewebptest = None

    if ctx.message.reference is not None:
        print("This is a reply")
        message = await channel.fetch_message(ctx.message.reference.message_id)
        print(message)
        print(message.attachments)
        print(message.embeds)
        if not (message.attachments or message.embeds):
            print("nothing found")
            workingtype = 0
            await ctx.send("No media found.")
            return workingtype, filetype
        id = message.id
    else:
        async for message in channel.history(limit=5):
            if message.attachments or message.embeds:
                #print(message)
                print(message.attachments)
                print(message.embeds)
                withattachments.append(message.id)
        if not withattachments:
            print("nothing found")
            workingtype = 0
            await ctx.send("No media found.")
            return workingtype, filetype
        id = withattachments[0]


    #print(withattachments)

    print(id)
    message = await channel.fetch_message(id)
    print(message)

    if message.attachments:
        await message.attachments[0].save(f"{workid}")
        filetype = str(message.attachments[0].content_type)
        print(filetype)
        match filetype:
            case "image/gif":
                workingtype = 3
            case "video/mp4":
                workingtype = 1
            case "video/quicktime":
                workingtype = 1
            case "image/png":
                workingtype = 2
            case "image/jpg":
                workingtype = 2
            case "image/jpeg":
                workingtype = 2
            case "image/webp":
                animewebptest = await IsAGif(workid)
                if animewebptest == True:
                    workingtype = 1
                elif animewebptest == False:
                    workingtype = 2
                else:
                    workingtype = 0
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
            print(f'trying attempt {attempt}')
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
                    if message.embeds[0].image.url != None:
                        req = requests.get(str(message.embeds[0].image.url), headers=hdr)
                case 3:
                    if message.embeds[0].image.proxy_url != None:
                        req = requests.get(str(message.embeds[0].image.proxy_url), headers=hdr)
                case 4:
                    if message.embeds[0].thumbnail.proxy_url != None:
                        req = requests.get(str(message.embeds[0].thumbnail.proxy_url), headers=hdr)
                case 10:
                    await ctx.send("No media found.")
                    workingtype = 0
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
                filetype = str(req.headers.get('Content-Type'))
                workingtype = 1
                found = 1
            elif "gif" in str(req.headers.get('Content-Type')):
                print("found gif")
                filetype = str(req.headers.get('Content-Type'))
                workingtype = 3
                found = 1
            elif "webp" in str(req.headers.get('Content-Type')):
                print("found webp")
                filetype = str(req.headers.get('Content-Type'))
                found = 1
            elif "jpeg" in str(req.headers.get('Content-Type')):
                print("found jpeg")
                filetype = str(req.headers.get('Content-Type'))
                workingtype = 2
                found = 1
            elif "png" in str(req.headers.get('Content-Type')):
                print("found png")
                filetype = str(req.headers.get('Content-Type'))
                workingtype = 2
                found = 1
            else:
                print(f"attempt {attempt} failed, moving on")
                attempt += 1
                workingtype = 0

        if req is not None:
            with open(f"{workid}", 'wb') as f:
                for chunk in req.iter_content(1024):
                    f.write(chunk)
            if filetype == "image/webp":
                animewebptest = await IsAGif(workid)
                print(f'animewebptest is {animewebptest}')
                if animewebptest == True:
                    workingtype = 1
                elif animewebptest == False:
                    workingtype = 2
                else:
                    workingtype = 0


    else:
        workingtype = 0
        await ctx.send("No media found.")

    #Just send the extension. It makes life easier
    filetype = mimetypes.guess_extension(filetype)
    return workingtype, filetype

async def getframerate(workid):
    frame = await asyncio.create_subprocess_shell(f'ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of default=noprint_wrappers=1:nokey=1 {workid}', stdout=asyncio.subprocess.PIPE)
    framerate = await frame.communicate()
    print(framerate)
    framerate = framerate[0].decode('ascii')
    framerate = framerate.strip()
    return framerate

async def splitframes(workid, filetype):
    #split input into series of pngs, falling back to magick for webp because fuck you google
    if filetype == ".webp":
        splitproc = await asyncio.create_subprocess_shell(f'magick {workid} ./{workid}-folder/frame%04d.png', stdout=asyncio.subprocess.PIPE)
    else:
        splitproc = await asyncio.create_subprocess_shell(f'ffmpeg -hide_banner -loglevel error -i {workid} -fps_mode passthrough ./{workid}-folder/frame%04d.png', stdout=asyncio.subprocess.PIPE)
    split = await splitproc.communicate()

async def makegif(workid, framerate):
    #Generate a gif based on the mass png modifications
    gifproc = await asyncio.create_subprocess_shell(f'ffmpeg -hide_banner -loglevel error -framerate {framerate} -i ./{workid}-folder/frame%04d.png {workid}.gif -y', stdout=asyncio.subprocess.PIPE)
    gif = await gifproc.communicate()

async def makevid(workid, framerate):
    #export all audio tracks to mov
    audioproc = await asyncio.create_subprocess_shell(f'ffmpeg -hide_banner -loglevel error -i ./{workid} -map a -c copy {workid}-audio.mov -y', stdout=asyncio.subprocess.PIPE)
    audio = await audioproc.communicate()

    #Create a video from all converted frames
    vidproc = await asyncio.create_subprocess_shell(f'ffmpeg -hide_banner -loglevel error -framerate {framerate} -i ./{workid}-folder/frame%04d.png -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -c:v libsvtav1 {workid}-video.mp4 -y', stdout=asyncio.subprocess.PIPE)
    vid = await vidproc.communicate()

    #Re-add audio back into video
    shuffleproc = await asyncio.create_subprocess_shell(f'ffmpeg -hide_banner -loglevel error -i {workid}-video.mp4 -i {workid}-audio.mov -c copy -map 0:v:0 -map 1:a {workid}.mp4 -y', stdout=asyncio.subprocess.PIPE)
    shuffle = await shuffleproc.communicate()

async def sizecheck(workid, filetype):
    #Check if we're over the max size for an upload on discord
    size = os.path.getsize(f'{workid}{filetype}')

    #Make a mini-gif in 480p as an attempt to salvage a massive file
    if size >= 20000000 and filetype == ".gif":
        gifresizeproc = await asyncio.create_subprocess_shell(f'ffmpeg -y -i "{workid}.gif" -filter_complex "fps=20,scale=480:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=32[p];[s1][p]paletteuse=dither=bayer" -loop 0 {workid}-mini.gif', stdout=asyncio.subprocess.PIPE)
        gifresize = await gifresizeproc.communicate()
        os.remove(f'{workid}.gif')
        os.replace(f'{workid}-mini.gif',f'{workid}.gif')

async def cleanup(workid):
    frame = await asyncio.create_subprocess_shell(f'rm -rf *{workid}*', stdout=asyncio.subprocess.PIPE)

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
async def explode(cts, arg1=None):
    pass

@bot.command(aliases=['deep'])
async def deepfry(ctx, arg1=None):
    workid = str(uuid.uuid4())
    output = await getmedia(ctx, workid)
    workingtype = output[0]
    filetype = output[1]

    contrast = 5
    audio = 0

    if arg1 is not None:
        if arg1.isdigit():
            print("custom contrast")
            contrast = int(arg1)
        elif arg1 == "help":
            await ctx.send("deepfry arg list\nany number: change contrast in deepfry output (default 5). Higher is scarier.\nsilent: turn video into gif (remove audio)\nhelp: see this")
            return
        elif arg1 == "silent":
            print(workingtype)
            workingtype = 3
            print(workingtype)

    if workingtype == 0:
        print("exiting, no data")
        return

    if workingtype == 1 or workingtype == 3:
        os.mkdir(f"./{workid}-folder")
        framerate = await getframerate(workid)
        print(framerate)

        await splitframes(workid, filetype)

        #Run mogrify in parallel for speed, wiggling variably with the math from earlier
        liquid = await asyncio.create_subprocess_shell(f'cd ./{workid}-folder; ls *.png | parallel mogrify -modulate 100,250,100 -sigmoidal-contrast {contrast},{contrast*14}% -unsharp 0x5 -quality 10 {{}}', stdout=asyncio.subprocess.PIPE)
        stdout, stderr = await liquid.communicate()

        if workingtype == 1:
            print("making a video")

            await makevid(workid, framerate)

            #Send it!
            await ctx.send(file=discord.File(f'{workid}.mp4'))

        if workingtype == 3:

            print("making a gif")

            await makegif(workid, framerate)

            await sizecheck(workid, ".gif")

            #Send it!
            await ctx.send(file=discord.File(f'{workid}.gif'))

        #Clean up all the scratch used in generation
        await cleanup(workid)


    if workingtype == 2:
        print("working on image")

        #Gather the dimensions of a single frame for max wackiness on the resizing
        with Image.open(f"./{workid}") as image:
            width, height = image.size

        #Run mogrify in parallel for speed, wiggling variably with the math from earlier
        liquid = await asyncio.create_subprocess_shell(f'mogrify -modulate 100,250,100 -sigmoidal-contrast {contrast},{contrast*14}% -unsharp 0x5 -quality 10 {workid}', stdout=asyncio.subprocess.PIPE)
        stdout, stderr = await liquid.communicate()

        os.replace(f'{workid}',f'{workid}{filetype}')

        #Send it!
        await ctx.send(file=discord.File(f'{workid}{filetype}'))

        #Cleanup
        await cleanup(workid)

@bot.command()
async def magik(ctx, arg1=None):
    workid = str(uuid.uuid4())
    output = await getmedia(ctx, workid)

    workingtype = output[0]
    filetype = output[1]
    print(filetype)

    if workingtype == 0:
        print("exiting, no data")
        return

    audio = 0
    print(output)
    #Only useful if we need more than one return variable]
    print(output[0])
    print(output[1])


    if arg1 is not None:
        if arg1.isdigit():
            print("custom contrast")
            contrast = int(arg1)
        elif arg1 == "help":
            await ctx.send("deepfry arg list\nany number: change contrast in deepfry output (default 5). Higher is scarier.\nsilent: turn video into gif (remove audio)\nhelp: see this")
            return
        elif arg1 == "silent":
            print(workingtype)
            workingtype = 3
            print(workingtype)

    if workingtype == 1 or workingtype == 3:
        os.mkdir(f"./{workid}-folder")
        framerate = await getframerate(workid)
        print(framerate)

        await splitframes(workid, filetype)

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

        if workingtype == 1:
            print("making a video")

            await makevid(workid, framerate)

            #Send it!
            await ctx.send(file=discord.File(f'{workid}.mp4'))

        if workingtype == 3:

            print("making a gif")

            await makegif(workid, framerate)

            await sizecheck(workid, ".gif")

            #Send it!
            await ctx.send(file=discord.File(f'{workid}.gif'))

        #Clean up all the scratch used in generation
        await cleanup(workid)

    if workingtype == 2:
        print("working on image")

        #Gather the dimensions of a single frame for max wackiness on the resizing
        with Image.open(f"./{workid}") as image:
            width, height = image.size

        #Calc some decent values to use randomly
        maxheightwiggle = round(height/2)
        maxwidthwiggle = round(width/2)

        minheightwiggle = round(height/3)
        minwidthwiggle = round(width/3)

        #Run mogrify in parallel for speed, wiggling variably with the math from earlier
        liquid = await asyncio.create_subprocess_shell(f'mogrify -liquid-rescale {width - random.randrange(minwidthwiggle,maxwidthwiggle)}x{height - random.randrange(minheightwiggle,maxheightwiggle)} {workid}', stdout=asyncio.subprocess.PIPE)
        stdout, stderr = await liquid.communicate()

        os.replace(f'{workid}',f'{workid}{filetype}')

        #Send it!
        await ctx.send(file=discord.File(f'{workid}{filetype}'))

        #Cleanup
        await cleanup(workid)

@tasks.loop(seconds=1, count=5)
async def testloop(ctx):
    print("hello")
    await ctx.send("hello")

@bot.command()
async def testloopcmd(ctx):
    testloop.start(ctx)

@bot.command()
async def chattest(ctx, arg1):
    sourcemessage = [
                {
                "role": "system",
                "content": "You are Mr.Krabs from the TV Show Spongebob Squarepants. Answer as closely as possible to what you would think he would answer, but keep it to 5 sentences max. You can exceed this if you are describing the environment, or actions taking place in a given response. The absolute max is 10 sentences."
                }
        ]
    global scratchmessage

    if arg1 is not None:
        if arg1 == "clear":
            scratchmessage = []
            await ctx.send("Cleared!")
            return

    if not scratchmessage:
        scratchmessage = sourcemessage

    print(sourcemessage)
    print("\n")
    print(scratchmessage)

    command = ctx.message.content

    command = command.replace("$chattest ","")

    chat = {}
    url = "http://localhost:9931/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": "Bearer no-key"}

    scratchmessage.append({"role": "user", "content": f'{command}'})

    chat['messages'] = scratchmessage

    try:
        response = requests.post(url, headers=headers, json=chat)
    except:
        await ctx.send("failed to reach server")
        return

    #print(response)
    #print(response.content)

    test = response.json()

    test = test['choices'][0]['message']['content']

    scratchmessage.append({"role": "assistant", "content": f'{test}'})

    print(test)

    await ctx.send(test)


# @bot.event
# async def on_ready():
#     testloop.start()
#     print("started")


bot.run('')

