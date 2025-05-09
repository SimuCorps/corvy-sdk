/**
 * CorvyBot Example - Echo Bot
 * This bot echoes back any message that includes the command prefix.
 */

const CorvyBot = require('./corvy-sdk');

// Replace these values with your actual bot token and API URL
const BOT_TOKEN = 'your_bot_token_here';
const API_URL = 'https://corvy.chat/api/v1';

// Define commands that the bot will respond to
const commands = [
  {
    prefix: '!echo',
    handler: (message) => {
      // Extract the content after the command
      const content = message.content.substring(message.content.indexOf('!echo') + 5).trim();
      return content ? `Echo: ${content}` : 'You said nothing!';
    }
  },
  {
    prefix: '!hello',
    handler: (message) => {
      return `Hello, ${message.user.username}! How are you today?`;
    }
  },
  {
    prefix: '!help',
    handler: () => {
      return 'Available commands: !echo [text], !hello, !help';
    }
  }
];

// Create and start the bot
const bot = new CorvyBot({
  apiToken: BOT_TOKEN,
  apiBaseUrl: API_URL,
  commands: commands
});

console.log('Starting echo bot...');
bot.start(); 