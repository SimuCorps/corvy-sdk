# Corvy Bot SDK

This directory contains official SDKs for building bots for the Corvy chat platform. These SDKs make it easy to create interactive bots that can respond to commands in chat rooms.

## Available SDKs

- [JavaScript SDK](#javascript-sdk)
- [Python SDK](#python-sdk)

## JavaScript SDK

### Installation

```bash
cd javascript
npm install
```

### Usage

```javascript
import { Client } from "../sdk/corvy.js";

const client = new Client({
    token: "your_token",
    prefix: ";", // default value
    devMode: true // default value (true = more detailed logging)
});

client.on("error", (err) => {
    console.error(err);
});

client.on("ready", (client) => {
    console.log(`${client.user.name} is now online!`);
    console.log(`I am in ${client.flocks.size} flocks.`);
});

client.registerCommand("ping", async (msg, client, args) => {
    return "Pong!";
});

client.login();
```

### Example Bot

See `javascript/docs/simple-bot.js` for a complete example bot.
<br />
See `javascript/docs/command-handler-example` for a complete command handler example bot.

## Python SDK

### Installation

```bash
pip install corvy_sdk
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

See `python/docs/example_bot.py` for a complete example bot.

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
