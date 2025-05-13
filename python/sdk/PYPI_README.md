# Corvy SDK
> Note: The Corvy SDKs are all officially sponsored, community maintained.

## Quickstart

Start by creating a CorvyBot:
```python
bot = CorvyBot("your_corvy_sdk_token")
```

Then, attach a command:
```python
@bot.command()
async def hello(message: Message):
    return f"Hello, {message.user.username}! How are you today?"
```

Lastly, start your bot:
```python
if __name__ == "__main__":
    bot.start() 
```