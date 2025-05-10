#!/usr/bin/env python3
# CorvyBot Example - Echo Bot
# This bot echoes back any message that includes the command prefix.

from corvy_sdk import CorvyBot

# Replace this values with your actual bot token
BOT_TOKEN = 'your_bot_token_here'

# Create the bot, so we can attach commands to it
bot = CorvyBot(BOT_TOKEN)

@bot.command() # Mark the function as a command
def echo(message):
    # Extract the content after the command
    command_pos = message['content'].lower().find('!echo')
    if command_pos != -1:
        content = message['content'][command_pos + 5:].strip()
        return "Echo: " + content if content else "You said nothing!"
    return "Echo command not found"

@bot.command()
def hello(message):
    return f"Hello, {message['user']['username']}! How are you today?"

@bot.command()
def help(_):
    return "Available commands: !echo [text], !hello, !help"

# Start the bot
if __name__ == "__main__":
    print('Starting echo bot...')
    bot.start() 