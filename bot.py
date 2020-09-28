# bot.py
import os
import discord

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN') #This grabs the discord token from a .env file within the same directory as the bot

#client = discord.Client()
bot = commands.Bot(command_prefix='!')

#@client.event
#async def on_ready():
#    print(f'{client.user} has connected to Discord!')



@bot.command(name='ness_test')
async def ness_test(test):
    
    await test.send("test")








#client.run(TOKEN)
bot.run(TOKEN)
