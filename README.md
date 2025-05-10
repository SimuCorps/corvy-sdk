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
gem install corvy_sdk-1.0.0.gem
```

### Usage

```ruby
require_relative 'corvy_sdk'

# Replace with your bot token and API base URL
BOT_TOKEN = 'your_bot_token_here'
API_URL = 'https://corvy.chat/api/v1'

# Define commands that the bot will respond to
commands = [
  {
    prefix: '!hello',
    handler: lambda do |message|
      "Hello, #{message['user']['username']}!"
    end
  }
]

# Create and start the bot
bot = CorvyBot.new({
  apiToken: BOT_TOKEN,
  apiBaseUrl: API_URL,
  commands: commands
})

bot.start
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

@bot.command()
async def hello(message: Message):
    return f"Hello, {message['user']['username']}! How are you today?"

# Start the bot
if __name__ == "__main__":
    bot.start() 
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