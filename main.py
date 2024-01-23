import os
import re
import discord
import aiohttp
import asyncio
import datetime
from discord.ext import commands
from webapp import keep_alive
from dotenv import load_dotenv

load_dotenv()
keep_alive()

API_URL_CONVERSATION = os.environ['API_URL_CONVERSATION']
HUGGINGFACE_TOKEN = os.environ['HUGGINGFACE_TOKEN']
DISCORD_TOKEN = os.environ['DISCORD_TOKEN']
HISTORY = 995875295359946762

intents = discord.Intents.default()
intents.messages = True

bot = commands.AutoShardedBot(command_prefix='', intents=intents)

conversation_history = {}  # Store conversation history


@bot.event
async def on_ready():
  print(f'Logged in as {bot.user}')
  await bot.change_presence(activity=discord.Activity(
      type=discord.ActivityType.watching, name="with brotAI | Conversational"))


@bot.event
async def on_message(message):
  if message.author == bot.user or message.author.id == bot.user.id or message.channel.id == HISTORY:
    return

  brot_pattern = r'\bbrot\b'
  if re.search(
      brot_pattern, message.content, re.IGNORECASE
  ) or bot.user in message.mentions or bot.user in message.reference.mentions:
    async with message.channel.typing():
      prompt = re.sub(brot_pattern, '', message.content, flags=re.IGNORECASE)
      context = conversation_history.get(
          message.channel.id, '')  # Get conversation history for the channel
      prompt_with_context = f"{context} {prompt}".strip()
      payload = {'inputs': {'text': prompt_with_context}}

      async with aiohttp.ClientSession() as session:
        async with session.post(
            API_URL_CONVERSATION,
            headers={'Authorization': f'Bearer {HUGGINGFACE_TOKEN}'},
            json=payload) as response:
          response_data = await response.json()
          bot_response = response_data.get('generated_text', '')

      await message.reply(bot_response)

      # Update conversation history for the channel
      conversation_history[
          message.channel.id] = f"{context} {prompt} {bot_response}".strip()

  await bot.process_commands(message)


async def main():
  await bot.start(DISCORD_TOKEN)


if __name__ == '__main__':
  keep_alive()
  asyncio.get_event_loop().run_until_complete(main())
