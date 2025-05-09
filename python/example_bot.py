#!/usr/bin/env python3
# CorvyBot Example - Echo Bot
# This bot echoes back any message that includes the command prefix.

from corvy_sdk import CorvyBot

# Replace these values with your actual bot token and API URL
BOT_TOKEN = 'your_bot_token_here'
API_URL = 'https://corvy.chat/api/v1'

# Helper function to handle the echo command
def handle_echo(message):
    # Extract the content after the command
    command_pos = message['content'].lower().find('!echo')
    if command_pos != -1:
        content = message['content'][command_pos + 5:].strip()
        return "Echo: " + content if content else "You said nothing!"
    return "Echo command not found"

# Helper function to handle the hello command
def handle_hello(message):
    return f"Hello, {message['user']['username']}! How are you today?"

# Helper function to handle the help command
def handle_help(_):
    return "Available commands: !echo [text], !hello, !help"

# Define commands that the bot will respond to
commands = [
    {
        'prefix': '!echo',
        'handler': handle_echo
    },
    {
        'prefix': '!hello',
        'handler': handle_hello
    },
    {
        'prefix': '!help',
        'handler': handle_help
    }
]

# Create and start the bot
bot = CorvyBot({
    'apiToken': BOT_TOKEN,
    'apiBaseUrl': API_URL,
    'commands': commands
})

if __name__ == "__main__":
    print('Starting echo bot...')
    bot.start() 