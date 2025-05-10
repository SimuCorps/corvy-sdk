# CorvyBot SDK - v2.0.0
# Client library for building Corvy bots

import aiohttp
import traceback
import json
import time
import signal
import sys
import asyncio
from typing import List, Dict, Callable, Any, Optional, Union

class CorvyBot:
    """
    Client library for building Corvy bots
    """
    
    def __init__(self, token: str, global_prefix: str = "!", api_base_url: str = "https://corvy.chat", api_path: str = "/api/v1"):
        """
        Create a new bot instance
        
        Args:
            token: Token for the Corvy API.
            global_prefix: The prefix for all commands. Defaults to an exclamation mark.
            api_base_url: The URL for the Corvy API.
        """
        self.commands: dict[str, Callable] = {}
        self.token = token
        self.global_prefix = global_prefix
        self.api_base_url = api_base_url
        self.api_path = api_path
        self.current_cursor = 0
        self.headers = {
            'Authorization': f"Bearer {token}",
            'Content-Type': 'application/json'
        }
        self.client_session: aiohttp.ClientSession | None = None

        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown_stub)
    
    def command(self, prefix: str | None = None):
        """Register a command.
        
        Args:
            prefix: The prefix of the command. Defaults to the name of the function with the global prefix beforehand."""
            
        def _decorator_inst(func: Callable):
            self.commands[prefix or f"{self.global_prefix}{getattr(func, '__name__', None)}"] = func
            return func # We don't wrap the function itself
        
        return _decorator_inst
    
    def start(self):
        """Start the bot and begin processing messages"""
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self._start_async())    
        except Exception as e:
            print(f"Failed to start bot loop: {str(e)}")
            traceback.print_exc()
            sys.exit(1)
    
    async def _start_async(self):
        """Start the bot, but in an async context."""
        try:
            print("Starting bot...")
            
            self.client_session = aiohttp.ClientSession(self.api_base_url, headers=self.headers)
            
            async with self.client_session.post(f"{self.api_path}/auth") as response:
                response_data = await response.json()
                print(f"Bot authenticated: {response_data['bot']['name']}")
        
            # Establish baseline (gets highest message ID but no messages)
            print("Establishing baseline with server...")
            
            async with self.client_session.get(f"{self.api_path}/messages", params={'cursor': 0}) as response:
                baseline_data = await response.json()
                # Save the cursor for future requests
                if baseline_data.get('cursor'):
                    self.current_cursor = baseline_data['cursor']
                    print(f"Baseline established. Starting with message ID: {self.current_cursor}")
            
            # Log command prefixes
            command_prefixes = [cmd for cmd in self.commands.keys()]
            print(f"Listening for commands: {', '.join(command_prefixes)}")
            
            await self._process_message_loop()
            
        except Exception as e:
            print(f"Failed to start bot: {str(e)}")
            traceback.print_exc()
            sys.exit(1)
    
    async def _process_message_loop(self):
        """Process messages in a loop"""
        while True:
            try:
                async with self.client_session.get(f"{self.api_path}/messages", params={'cursor': self.current_cursor}) as response:
                    data = await response.json()

                    # Update cursor
                    if data.get('cursor'):
                        self.current_cursor = data['cursor']

                    # Process each new message
                    for message in data.get('messages', []):
                        # Skip bot messages
                        if message.get('user', {}).get('is_bot', False):
                            continue

                        print(f"Message from {message['user']['username']} in {message['flock_name']}/{message['nest_name']}: {message['content']}")

                        # Check for commands
                        await self._handle_command(message)
                
                # Wait before checking again
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Error fetching messages: {str(e)}")
                traceback.print_exc()
                await asyncio.sleep(5)  # Longer delay on error
    
    async def _handle_command(self, message: Dict[str, Any]):
        """
        Handle command messages
        
        Args:
            message: Message object
        """
        message_content: str = message['content'].lower()
        # Check each command prefix
        for prefix, handler in self.commands.items():
            if message_content.startswith(prefix.lower()):
                print(f"Command detected: {prefix}")
                
                # Generate response using the command handler
                response_content = await handler(message)
                
                # Send the response
                await self.send_message(message['flock_id'], message['nest_id'], response_content)
                
                # Stop after first matching command
                break
            
    async def send_message(self, flock_id: Union[str, int], nest_id: Union[str, int], content: str):
        """
        Send a message
        
        Args:
            flock_id: Flock ID
            nest_id: Nest ID
            content: Message content
        """
        try:
            print(f'Sending message: "{content}"')
            
            async with self.client_session.post(f"{self.api_path}/flocks/{flock_id}/nests/{nest_id}/messages", json={'content': content}) as response:
                pass
                
        except Exception as e:
            print(f"Failed to send message: {str(e)}")
            
    def _handle_shutdown_stub(self, sig, frame):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._handle_shutdown(sig, frame))
        except RuntimeError:
            asyncio.run(self._handle_shutdown(sig, frame))

    async def _handle_shutdown(self, sig, frame):
        """Handle graceful shutdown"""
        print("Bot shutting down...")
        await self.client_session.close()
        try:
            asyncio.get_running_loop().stop()
        except RuntimeError:
            pass
        sys.exit(0)