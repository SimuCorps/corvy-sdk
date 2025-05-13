#!/usr/bin/env python3
# CorvyBot Example - Echo Bot
# This bot echoes back any message that includes the command prefix.

from typing import Annotated
from corvy_sdk import CorvyBot, Greedy, Message

# Replace this value with your actual bot token
BOT_TOKEN = 'your_bot_token_here'

# Create the bot, so we can attach commands to it
bot = CorvyBot(BOT_TOKEN)

@bot.command() # Mark the function as a command
async def echo(message: Message, echo_string: Annotated[str, Greedy]): # We annotate the string as Greedy so that we get the entire text after the command
    if echo_string == "": # The greedy string got nothing 
        return "You said nothing!"
    return "Echo: " + echo_string

@bot.command()
async def hello(message: Message):
    return f"Hello, {message.user.username}! How are you today?"

@bot.command() 
async def help(_message: Message):
    return "Available commands: !echo [text], !hello, !help"

# Create an event to catch potential exceptions
@bot.event("on_command_exception")
async def on_exc(command: str, message: Message, exception: Exception):
    await bot.send_message(message.flock_id, message.nest_id, f"The command {command} errored out! ({exception})")

# Start the bot
if __name__ == "__main__":
    print('Starting echo bot...')
    bot.start() 