# Corvy Bot SDK

This directory contains official SDKs for building bots for the Corvy chat platform. These SDKs make it easy to create interactive bots that can respond to commands in chat rooms.

## Available SDKs

- [JavaScript SDK](#javascript-sdk)
- [Ruby SDK](#ruby-sdk)
- [Python SDK](#python-sdk)

## JavaScript SDK

### Installation

```bash
cd javascript
npm install
```

### Usage

```javascript
const CorvyBot = require('./corvy-sdk');

// Replace with your bot token and API base URL
const BOT_TOKEN = 'your_bot_token_here';
const API_URL = 'https://corvy.chat/api/v1';

// Define commands that the bot will respond to
const commands = [
  {
    prefix: '!hello',
    handler: (message) => {
      return `Hello, ${message.user.username}!`;
    }
  }
];

// Create and start the bot
const bot = new CorvyBot({
  apiToken: BOT_TOKEN,
  apiBaseUrl: API_URL,
  commands: commands
});

bot.start();
```

### Example Bot

See `javascript/example-bot.js` for a complete example bot.

## Ruby SDK

### Installation

```bash
cd ruby
# If you're using Bundler
bundle install
# Or install the gem directly
gem build corvy_sdk.gemspec
gem install corvy_sdk-1.5.1.gem
```

### Usage

```ruby
require_relative 'corvy_sdk'

# Replace with your bot token
BOT_TOKEN = 'your_bot_token_here'

# Create the bot instance
bot = CorvyBot.new(BOT_TOKEN)

# Define commands using the decorator pattern
hello_command = bot.command()
hello_command.call(
  define_method(:hello) do |message|
    "Hello, #{message.user.username}!"
  end
)

# Register an event handler
message_event = bot.event("on_message")
message_event.call(
  define_method(:handle_message) do |message|
    puts "Received: #{message.content}"
  end
)

# Start the bot
bot.start
```

### Command Parameters and Types

The Ruby SDK now supports advanced parameter parsing:

```ruby
# Command with parameter support
echo_command = bot.command()
echo_command.call(
  define_method(:echo) do |message, echo_string = ""|
    if echo_string.empty?
      "You said nothing!"
    else
      "Echo: #{echo_string}"
    end
  end
)

# Exception handling with events
command_exception_event = bot.event("on_command_exception")
command_exception_event.call(
  define_method(:on_exc) do |command, message, exception|
    bot.send_message(message.flock_id, message.nest_id, 
      "Error in command #{command}: #{exception}")
  end
)
```

### Example Bot

See `ruby/example_bot.rb` for a complete example bot.

## Python SDK

### Installation

```bash
cd python
pip install -e .
```

### Usage

```python
from corvy_sdk import CorvyBot, Message

# Replace this value with your actual bot token
BOT_TOKEN = 'your_bot_token_here'

# Create the bot
bot = CorvyBot(BOT_TOKEN)

# Create a command
@bot.command()
async def hello(message: Message):
    return f"Hello, {message.user.username}! How are you today?"

# Start the bot
if __name__ == "__main__":
    bot.start() 
```

### Command Parameters and Types

Similarly to the Ruby SDK, the Python SDK supports automatic parameter passing:

```python
from corvy_sdk import CorvyBot, Greedy
from typing import Annotated

@bot.command() # Mark the function as a command
async def echo(message: Message, echo_string: Annotated[str, Greedy]): 
                                 # We annotate the string as Greedy so that we get the entire text after the command. If we don't, it'll only get one word.
    if echo_string == "": # The greedy string got nothing 
        return "You said nothing!"
    return "Echo: " + echo_string
```

### Events

The Python SDK also supports five events:
- `on_message_raw` - triggers on every message, before commands are called. 
  - Has one parameter (a Message).
- `on_message` - triggers on messages that weren't ran as commands. 
  - Has one parameter (a Message).
- `prestart` - triggers before any of the bot is configured.
  - Has one parameter (the CorvyBot).
- `start` - triggers before the message loop begins.
  - Has one parameter (the CorvyBot).
- `on_command_exception` - triggers if a command errors out, or if automatic parameters fail to parse; failures can occur due to them being invalid or the user failing to put in all of them.
  - Has three parameters (the command called as a string, a Message object, and the Exception object).

```python
# Create an event to catch potential exceptions
@bot.event("on_command_exception")
async def on_exc(command: str, message: Message, exception: Exception):
    await bot.send_message(message.flock_id, message.nest_id, f"The command {command} errored out! ({exception})")
```

### Example Bot

See `python/example_bot.py` for a complete example bot.

## API Documentation

All SDKs interact with the Corvy API via the following endpoints:

- `POST /auth` - Authenticate the bot
- `GET /messages` - Get new messages (with cursor)
- `POST /flocks/:flock_id/nests/:nest_id/messages` - Send a response message

## Testing Your Bot

1. Create a bot in the Corvy developer portal
2. Get the bot's API token
3. Replace the placeholder token in the example code
4. Run your bot
5. Send messages in a chat room where the bot is present

## Getting Help

For more information or assistance, please contact the Corvy development team. 