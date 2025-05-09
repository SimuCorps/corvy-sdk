#!/usr/bin/env ruby
# CorvyBot Example - Echo Bot
# This bot echoes back any message that includes the command prefix.

require_relative 'corvy_sdk'

# Replace these values with your actual bot token and API URL
BOT_TOKEN = 'your_bot_token_here'
API_URL = 'https://corvy.chat/api/v1'

# Define commands that the bot will respond to
commands = [
  {
    prefix: '!echo',
    handler: lambda do |message|
      # Extract the content after the command
      content = message['content'].slice(message['content'].downcase.index('!echo') + 5..-1).strip
      content.empty? ? 'You said nothing!' : "Echo: #{content}"
    end
  },
  {
    prefix: '!hello',
    handler: lambda do |message|
      "Hello, #{message['user']['username']}! How are you today?"
    end
  },
  {
    prefix: '!help',
    handler: lambda do |_|
      'Available commands: !echo [text], !hello, !help'
    end
  }
]

# Create and start the bot
bot = CorvyBot.new({
  apiToken: BOT_TOKEN,
  apiBaseUrl: API_URL,
  commands: commands
})

puts 'Starting echo bot...'
bot.start 