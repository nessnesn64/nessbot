# This example requires the 'message_content' intent.

import discord
#from discord import app_commands
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
#client = discord.Client(intents=intents)

bot = commands.Bot(command_prefix='$',intents=intents)
#tree = app_commands.CommandTree(bot)

scratchmessage = []

#Function to determine if a webp is a video or image. Fuck you Google.
async def IsAGif(workid):
    try:
        MediaFile = Image.open(f'{workid}')
        Index = 0
        for Frame in ImageSequence.Iterator(MediaFile):
            Index += 1
            print(Index)
        if Index > 1: #Must mean the the .webp is a gif because it has more than one frame
            print("webp is animated")
            return True
        else: #Must mean that the .webp has 1 frame which makes it a image
            print("webp is image")
            return False
    except: #If the .webp can't be opened then it is most likely not a .gif or .webp
        return None

#General function for gathering media from embeds or attachments. Updated to v2 for slash command support.
async def getmedia2(interaction, workid, message=None):
    print(interaction)
    print(message)
    #Create a header to spoof firefox to help with pesky downloads that block python requests
    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

    #Get the channel details with the passed context
    channel = interaction.channel

    #Set an null array for attachments in the last 5 messages
    withattachments = []

    #Set a variable to determine between video/image. 1 = Video, 2 = Image
    workingtype = None

    #Set found = 0 to allow for searching embeds
    found = 0

    attempt = 0

    filetype = None
    animewebptest = None

    if message is not None:
        print("This is a reply")
        print(message)
        print(message.attachments)
        print(message.embeds)
        if not (message.attachments or message.embeds):
            print("nothing found")
            workingtype = 0
            await interaction.response.send_message("No media found.")
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
            await interaction.response.send_message("No media found.")
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
        if "video" in filetype:
            print("checking for audio")
            audiotracks = await getaudiotracks(workid)
            print(audiotracks)

            if audiotracks == 0:
                workingtype = 3
            else:
                workingtype = 1
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
                    await interaction.followup.send("No media found.")
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
        if "video" in filetype:
            print("checking for audio")
            audiotracks = await getaudiotracks(workid)
            print(audiotracks)

            if audiotracks == 0:
                workingtype = 3
            else:
                workingtype = 1



    else:
        workingtype = 0
        await ctx.send("No media found.")

    #Just send the extension. It makes life easier
    filetype = mimetypes.guess_extension(filetype)
    return workingtype, filetype

async def getaudiotracks(workid):
    tracks = await asyncio.create_subprocess_shell(f'ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 file:{workid} | wc -w', stdout=asyncio.subprocess.PIPE)
    numtracks = await tracks.communicate()
    numtracks = numtracks[0].decode('ascii')
    numtracks = numtracks.strip()

    numtracks = int(numtracks)

#    print(f'{numtracks} audio tracks')
    return numtracks

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

async def deepfrying(interaction, contrast, message=None):
    await interaction.response.defer()
    print(interaction)

    workid = str(uuid.uuid4())

    if message is not None:
        output = await getmedia2(interaction, workid, message)
    else:
        output = await getmedia2(interaction, workid)

    workingtype = output[0]
    filetype = output[1]

    print(contrast)
    audio = 0

    print(contrast)

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
            await interaction.followup.send(file=discord.File(f'{workid}.mp4'))

        if workingtype == 3:

            print("making a gif")

            await makegif(workid, framerate)

            await sizecheck(workid, ".gif")

            #Send it!
            await interaction.followup.send(file=discord.File(f'{workid}.gif'))

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
        await interaction.followup.send(file=discord.File(f'{workid}{filetype}'))

        #Cleanup
        await cleanup(workid)

async def magiking(interaction, message=None):
    await interaction.response.defer()
    workid = str(uuid.uuid4())

    if message is not None:
        output = await getmedia2(interaction, workid, message)
    else:
        output = await getmedia2(interaction, workid)
    workingtype = output[0]
    filetype = output[1]

    if workingtype == 0:
        print("exiting, no data")
        return

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
            await interaction.followup.send(file=discord.File(f'{workid}.mp4'))

        if workingtype == 3:

            print("making a gif")

            await makegif(workid, framerate)

            await sizecheck(workid, ".gif")

            #Send it!
            await interaction.followup.send(file=discord.File(f'{workid}.gif'))

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
        await interaction.followup.send(file=discord.File(f'{workid}{filetype}'))

        #Cleanup
        await cleanup(workid)

async def reversing(interaction, message=None):
    await interaction.response.defer()
    workid = str(uuid.uuid4())

    if message is not None:
        output = await getmedia2(interaction, workid, message)
    else:
        output = await getmedia2(interaction, workid)

    workingtype = output[0]
    filetype = output[1]

    if workingtype == 0:
        print("exiting, no data")
        return

    if workingtype == 2:
        print("can't reverse an image")
        await interaction.followup.send("This command does nothing with images, please submit a gif or video")

    if workingtype == 1 or workingtype == 3:
        if workingtype == 1:
            reverseffmpeg = await asyncio.create_subprocess_shell(f'ffmpeg -hide_banner -loglevel error -i {workid} -vf reverse -af areverse {workid}.mp4', stdout=asyncio.subprocess.PIPE)
            stdout, stderr = await reverseffmpeg.communicate()

            await interaction.followup.send(file=discord.File(f'{workid}.mp4'))
        elif workingtype == 3:
            reverseffmpeg = await asyncio.create_subprocess_shell(f'ffmpeg -hide_banner -loglevel error -i {workid} -vf reverse {workid}.gif', stdout=asyncio.subprocess.PIPE)
            stdout, stderr = await reverseffmpeg.communicate()
            await interaction.followup.send(file=discord.File(f'{workid}.gif'))

    await cleanup(workid)

async def exploding(interaction, factor, flip=False, message=None):
    await interaction.response.defer()
    workid = str(uuid.uuid4())

    if message is not None:
        output = await getmedia2(interaction, workid, message)
    else:
        output = await getmedia2(interaction, workid)

    workingtype = output[0]
    filetype = output[1]

    plodevalue = factor
    if factor != -1.0 and flip is False:
        plodevalue = factor * -1

    if factor != 0.5 and flip is True:
        plodevalue = factor * 0.5

    if workingtype == 0:
        print("exiting, no data")
        return

    if workingtype == 2:
        print("working on image")

        #Run mogrify in parallel for speed, wiggling variably with the math from earlier
        plode = await asyncio.create_subprocess_shell(f'mogrify -implode {plodevalue} {workid}', stdout=asyncio.subprocess.PIPE)
        stdout, stderr = await plode.communicate()

        os.replace(f'{workid}',f'{workid}{filetype}')

        #Send it!
        await interaction.followup.send(file=discord.File(f'{workid}{filetype}'))

        #Cleanup
        await cleanup(workid)

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
        plode = await asyncio.create_subprocess_shell(f'cd ./{workid}-folder; ls *.png | parallel mogrify -implode {plodevalue} {{}}', stdout=asyncio.subprocess.PIPE)
        stdout, stderr = await plode.communicate()

        if workingtype == 1:
            print("making a video")

            await makevid(workid, framerate)

            #Send it!
            await interaction.followup.send(file=discord.File(f'{workid}.mp4'))

        if workingtype == 3:

            print("making a gif")

            await makegif(workid, framerate)

            await sizecheck(workid, ".gif")

            #Send it!
            await interaction.followup.send(file=discord.File(f'{workid}.gif'))

        #Clean up all the scratch used in generation
        await cleanup(workid)

async def tinting(interaction, color, factor, message=None):
    await interaction.response.defer()
    workid = str(uuid.uuid4())

    if message is not None:
        output = await getmedia2(interaction, workid, message)
    else:
        output = await getmedia2(interaction, workid)

    workingtype = output[0]
    filetype = output[1]

    colorvalue = color
    tintvalue = factor
    print(colorvalue)
    print(tintvalue)

    if workingtype == 0:
        print("exiting, no data")
        return

    if workingtype == 2:
        print("working on image")

        #Run mogrify in parallel for speed, wiggling variably with the math from earlier
        tint = await asyncio.create_subprocess_shell(f'mogrify -fill {colorvalue} -tint {tintvalue} {workid}', stdout=asyncio.subprocess.PIPE)
        stdout, stderr = await tint.communicate()

        os.replace(f'{workid}',f'{workid}{filetype}')

        #Send it!
        await interaction.followup.send(file=discord.File(f'{workid}{filetype}'), content=f'tint: {colorvalue}, factor: {tintvalue}')

        #Cleanup
        await cleanup(workid)

    if workingtype == 1 or workingtype == 3:
        os.mkdir(f"./{workid}-folder")
        framerate = await getframerate(workid)
        print(framerate)

        await splitframes(workid, filetype)

        #Run mogrify in parallel for speed, wiggling variably with the math from earlier
        tint = await asyncio.create_subprocess_shell(f'cd ./{workid}-folder; ls *.png | parallel mogrify -fill {colorvalue} -tint {tintvalue} {{}}', stdout=asyncio.subprocess.PIPE)
        stdout, stderr = await tint.communicate()

        if workingtype == 1:
            print("making a video")

            await makevid(workid, framerate)

            #Send it!
            await interaction.followup.send(file=discord.File(f'{workid}.mp4'), content=f'tint: {colorvalue}, factor: {tintvalue}')

        if workingtype == 3:

            print("making a gif")

            await makegif(workid, framerate)

            await sizecheck(workid, ".gif")

            #Send it!
            await interaction.followup.send(file=discord.File(f'{workid}.gif'), content=f'tint: {colorvalue}, factor: {tintvalue}')

        #Clean up all the scratch used in generation
        await cleanup(workid)
# async def send_image():

@bot.tree.command(name='nessping', description='testcommand')
async def testslash(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@bot.command()
async def response(ctx):
    print("test command")
    await ctx.send(channel)

@bot.command()
async def image(ctx):
    print("image command")
    await ctx.send(file=discord.File('test.png'))

@bot.tree.command(name='deep', description='deepfry an image')
async def deepfry(interaction: discord.Interaction, contrast: int = 5):
    await deepfrying(interaction, contrast)

@bot.tree.context_menu(name='deep')
async def deepfry_menu(interaction: discord.Interaction, message: discord.Message):
    contrast = 5
    await deepfrying(interaction, contrast)

@bot.tree.command(name='magik', description='wacky content-aware scaling')
async def magik(interaction: discord.Interaction):
    await magiking(interaction)

@bot.tree.context_menu(name='magik')
async def magik_menu(interaction: discord.Interaction, message: discord.Message):
    await magiking(interaction, message)

@bot.tree.command(name='reverse', description='reverse video or gif')
async def reverse(interaction: discord.Interaction):
    await reversing(interaction)

@bot.tree.context_menu(name='reverse')
async def reverse_menu(interaction: discord.Interaction, message: discord.Message):
    await reversing(interaction, message)

@bot.tree.command(name='explode', description='BOOM')
async def explode(interaction: discord.Interaction, factor: float = -1.0):
    await exploding(interaction, factor)

@bot.tree.context_menu(name='explode')
async def explode_menu(interaction: discord.Interaction, message: discord.Message):
    factor = -1.0
    flip = False
    await exploding(interaction, factor, flip, message)

@bot.tree.command(name='implode', description='ZOOP')
async def implode(interaction: discord.Interaction, factor: float = 0.5):
    flip = True
    await exploding(interaction, factor, flip)

@bot.tree.context_menu(name='implode')
async def implode_menu(interaction: discord.Interaction, message: discord.Message):
    factor = 0.5
    flip = True
    await exploding(interaction, factor, flip, message)

@bot.tree.command(name='tint', description='Add a tint to an image')
async def tint(interaction: discord.Interaction, color: str = "green", factor: int = 100):
    await tinting(interaction, color, factor)


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

@bot.event
async def on_ready():
    guildid=discord.Object(id=231475464055685121)
    print(guildid)
    await bot.tree.sync(guild=guildid)
    await bot.tree.sync()
    # print "ready" in the console when the bot is ready to work
    print("ready")

# @bot.event
# async def on_ready():
#     testloop.start()
#     print("started")


bot.run('')

