#!/usr/bin/env ruby
# CorvyBot Example - Echo Bot
# This bot echoes back any message that includes the command prefix.

require_relative 'corvy_sdk'

# Replace this value with your actual bot token
BOT_TOKEN = 'your_bot_token_here'

# Create the bot, so we can attach commands to it
bot = CorvyBot.new(BOT_TOKEN)

# Mark the method as a command
echo_command = bot.command()
echo_command.call(
  # The command name will be "!echo" by default
  # We want to echo the entire message after the command
  define_method(:echo) do |message, echo_string = ""|
    if echo_string.empty?
      "You said nothing!"
    else
      "Echo: #{echo_string}"
    end
  end
)

# Another way to define a command
hello_command = bot.command()
hello_command.call(
  define_method(:hello) do |message|
    "Hello, #{message.user.username}! How are you today?"
  end
)

# Help command
help_command = bot.command()
help_command.call(
  define_method(:help) do |_message|
    "Available commands: !echo [text], !hello, !help"
  end
)

# Create an event to catch potential exceptions
command_exception_event = bot.event("on_command_exception")
command_exception_event.call(
  define_method(:on_exc) do |command, message, exception|
    bot.send_message(message.flock_id, message.nest_id, "The command #{command} errored out! (#{exception})")
  end
)

# Start the bot
if __FILE__ == $PROGRAM_NAME
  puts 'Starting echo bot...'
  bot.start
end 