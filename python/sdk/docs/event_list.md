# Event Listing

The Python SDK supports five events:

## `on_message_raw` 
`on_message_raw` triggers on every message, before commands are called. 

### Example
```python
@bot.event("on_message_raw")
async def on_message_raw(message: Message):
    if message.user.is_bot: # This can be true, since this is called before bots are excluded.
        match message.user.username:
            case "Perihelion":
                await bot.send_message(message.flock_id, message.nest_id, f"Hello, Perihelion!")
            case _:
                await bot.send_message(message.flock_id, message.nest_id, f"Hello, bot!")
```

## `on_message` 
`on_message` triggers on messages that weren't ran as commands and that weren't made by bots. 

### Example
```python
@bot.event("on_message")
async def on_message(message: Message):
    if "hello" in message.content:
        bot.send_message(message.flock_id, message.nest_id, f"Hello!")
```

## `prestart`
`prestart` triggers before any of the bot is configured.

### Example
```python
@bot.event("prestart")
async def prestart(bot: CorvyBot):
    bot.db = TotallyRealDBService("data.db")
    bot.db.initialize()
```

## `start`
`start` triggers before the message loop begins. 
It is recommended to use this and not `prestart`, since `prestart` has the bot uninitialized.

### Example
```python
@bot.event("start")
async def start(bot: CorvyBot):
    async with bot.client_session.post(f"{self.api_path}/auth") as response:
        response_data = await response.json()
        print(f"Bot authenticated: {response_data['bot']['name']}")
```

## `on_command_exception`
`on_command_exception` triggers if a command errors out.
This includes automatic parameters failimh to parse; failures can occur due to them being invalid or the user failing to put in all of them.

### Example
```python
@bot.event("on_command_exception")
async def on_exc(command: str, message: Message, exception: Exception):
    await bot.send_message(message.flock_id, message.nest_id, f"The command {command} errored out! ({exception})")
```