import asyncio
from datetime import datetime
import signal
import sys
import traceback
from typing import Awaitable, Callable
import logging
import aiohttp
from .messages import Message, MessageUser, MessageFlock, MessageNest
from .command_parsing import parse_args
from .default_logger import get_pretty_logger
from .state import ConnectionState

logger = get_pretty_logger("corvy_sdk")


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
        self.connection_state: ConnectionState | None = None
        self.events: dict[str, list[Awaitable]] = {}
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown_stub)
    
    def command(self, prefix: str | None = None):
        """Register a command.
        
        Args:
            prefix: The prefix of the command. Defaults to the name of the function with the global prefix beforehand."""
            
        def _decorator_inst(func: Awaitable):
            self.commands[prefix or f"{self.global_prefix}{getattr(func, '__name__', None)}"] = func
            return func # We don't wrap the function itself yet
        
        return _decorator_inst
    
    def event(self, event: str | None = None):
        """Register an event.
        
        Args:
            event: The event to register to. Defaults to the name of the function."""
        
        def _decorator_inst(func: Awaitable):
            event_name = event or getattr(func, '__name__', None)
            # If the event key doesn't yet exist, create it
            if not self.events.get(event_name, False):
                self.events[event_name] = []
            self.events[event_name].append(func)
            return func # We don't wrap the function itself
        
        return _decorator_inst
    
    def start(self):
        logging.basicConfig()
        """Start the bot and begin processing messages"""
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self._start_async())    
        except Exception as e:
            logger.exception(f"Failed to start bot loop: {str(e)}")
    
    async def _start_async(self):
        """Start the bot, but in an async context."""
        try:
            logger.debug("Running prestart events...")
            
            # Run prestart events
            events = self.events.get("prestart", [])
            for event in events:
                await event(self)

            logger.debug("Starting bot...")
            
            self.connection_state = ConnectionState(aiohttp.ClientSession(self.api_base_url, headers=self.headers), self.api_path)
            
            async with self.connection_state.client_session.post(f"{self.api_path}/auth") as response:
                response_data = await response.json()
                logger.info(f"Bot authenticated: {response_data['bot']['name']}")
        
            # Establish baseline (gets highest message ID but no messages)
            logger.debug("Establishing baseline with server...")
            
            async with self.connection_state.client_session.get(f"{self.api_path}/messages", params={'cursor': 0}) as response:
                baseline_data = await response.json()
                # Save the cursor for future requests
                if baseline_data.get('cursor'):
                    self.current_cursor = baseline_data['cursor']
                    logger.debug(f"Baseline established. Starting with message ID: {self.current_cursor}")
            
            # Log command prefixes
            command_prefixes = [cmd for cmd in self.commands.keys()]
            logger.debug(f"Listening for commands: {', '.join(command_prefixes)}")
            
            logger.debug("Running start events...")
            
            # Runstart events
            events = self.events.get("start", [])
            for event in events:
                await event(self)
            
            logger.debug("Running message loop...")
            
            await self._process_message_loop()
            
        except Exception as e:
            logger.exception(f"Failed to start bot: {str(e)}")
    
    async def _process_message_loop(self):
        """Process messages in a loop"""
        while True:
            try:
                async with self.connection_state.client_session.get(f"{self.api_path}/messages", params={'cursor': self.current_cursor}) as response:
                    data = await response.json()

                    # Update cursor
                    if data.get('cursor'):
                        self.current_cursor = data['cursor']

                    # Process each new message
                    for message in data.get('messages', []):
                        
                        msg_user = MessageUser(message["user"]["id"], message["user"]["username"], message["user"]["is_bot"], message["user"].get("photo_url", None)).attach_state(self.connection_state)
                        msg_flock = MessageFlock(message["flock_id"], message["flock_name"]).attach_state(self.connection_state)
                        msg_nest = MessageNest(message["nest_id"], msg_flock, message["nest_name"]).attach_state(self.connection_state)
                        
                        message = Message(message["id"], message["content"], msg_flock, msg_nest, datetime.strptime(message["created_at"], "%Y-%m-%dT%H:%M:%SZ"), msg_user).attach_state(self.connection_state)
                        
                        # Run on_message_raw events
                        events = self.events.get("on_message_raw", [])
                        for event in events:
                            await event(message)
                            
                        # Skip bot messages
                        if message.user.is_bot:
                            continue

                        logger.debug(f"Message from {message.user.username} in {message.flock_name}/{message.nest_name} ({message.flock_id}/{message.nest_id}): {message.content}")

                        # Check for commands
                        was_command = await self._handle_command(message)
                        # If it was a command, skip
                        if was_command:
                            continue
                        # Run on_message events
                        events = self.events.get("on_message", [])
                        for event in events:
                            await event(message)
                
                # Wait before checking again
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.exception(f"Error fetching messages: {str(e)}")
                traceback.print_exc()
                await asyncio.sleep(5)  # Longer delay on error
    
    async def _handle_command(self, message: Message) -> bool:
        """
        Handle command messages
        
        Args:
            message: Message object
        """
        message_content: str = message.content.lower()
        # Check each command prefix
        for prefix, handler in self.commands.items():
            if message_content.startswith(prefix.lower() + " "):
                logger.debug(f"Command detected: {prefix}")
                
                # Generate response using the command handler, if we don't get an error
                try:
                    args = parse_args(handler, message.content.replace(prefix, "", 1).strip(), message)
                    response_content = await handler(*args)
                except Exception as e:
                    events = self.events.get("on_command_exception", [])
                    for event in events:
                        await event(prefix, message, e)
                    return False
                    
                # Send the response
                await self.send_message(message.flock_id, message.nest_id, response_content)
                
                # Return true after first matching command
                return True
        # No commands were ran, so return false (we didn't run a command)
        return False
        
    async def send_message(self, flock_id: int, nest_id: int, content: str):
        """
        Send a message
        
        Args:
            flock_id: Flock ID
            nest_id: Nest ID
            content: Message content
        """
        try:
            logger.debug(f'Sending message: "{content}"')
            
            async with self.connection_state.client_session.post(f"{self.api_path}/flocks/{flock_id}/nests/{nest_id}/messages", json={'content': content}) as response:
                response.raise_for_status()
                
        except Exception as e:
            logger.exception(f"Failed to send message: {str(e)}")
            
    def _handle_shutdown_stub(self, sig, frame):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._handle_shutdown(sig, frame))
        except RuntimeError:
            asyncio.run(self._handle_shutdown(sig, frame))

    async def _handle_shutdown(self, sig, frame):
        """Handle graceful shutdown"""
        logger.info("Bot shutting down...")
        await self.connection_state.client_session.close()
        try:
            asyncio.get_running_loop().stop()
        except RuntimeError:
            pass
        sys.exit(0)