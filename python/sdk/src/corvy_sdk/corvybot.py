import asyncio
from datetime import datetime, timezone
import signal
import sys
from typing import Awaitable, Callable
import logging
from warnings import deprecated
import aiohttp
import json
from websockets import ConnectionClosed
from websockets.asyncio.client import connect
from .messages import Message, MessageUser
from .nest import PartialNest
from .flock import PartialFlock, Flock
from .command_parsing import parse_args
from .default_logger import get_pretty_logger
from .state import ConnectionState

logger = get_pretty_logger("corvy_sdk")


class CorvyBot:
    """
    Client library for building Corvy bots
    """
    
    def __init__(self, token: str, global_prefix: str = "!", api_base_url: str = "https://corvy.chat", api_path: str = "/api/v2"):
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
        self.auth_details: dict | None = None
        self.ws_keepalive_id: int = 0
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown_stub)
    
    def command(self, name: str | None = None, include_global_prefix: bool = True, aliases: list[str] | None = None):
        """Register a command.
        
        Args:
            name: The name of the command. Defaults to the name of the function.
            include_global_prefix: Notes if the global prefix should be included in the command name. True by default.
            aliases: A list of aliases for the command."""
            
        def _decorator_inst(func: Awaitable):
            if name is None:
                prefix = getattr(func, '__name__', "")
            else:
                prefix = name
            if include_global_prefix:
                prefix = f"{self.global_prefix}{prefix}"
            self.commands[prefix] = func
            if aliases:
                for alias in aliases:
                    if include_global_prefix:
                        self.commands[f"{self.global_prefix}{alias}"] = func
                    else:
                        self.commands[alias] = func
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
            client_session = aiohttp.ClientSession(self.api_base_url, headers=self.headers)
            response_data = {}
            
            async with client_session.post(f"{self.api_path}/auth") as response:
                response_data = await response.json()
                logger.info(f"Bot authenticated: {response_data['bot']['name']}")

            self.auth_details = response_data
            
            # Connect to websocket
            websocket = await connect(response_data["websocket"]["url"])
            await websocket.send(json.dumps(
                {
                    "topic": response_data["websocket"]["channel"],
                    "event": "phx_join",
                    "payload": {"token": self.token},
                    "ref": "1"
                }
            ))
            self.connection_state = ConnectionState(aiohttp.ClientSession(self.api_base_url, headers=self.headers), websocket, response_data["websocket"]["channel"], self.api_path)
            asyncio.create_task(self._keepalive())
            # Log command prefixes
            command_prefixes = [cmd for cmd in self.commands.keys()]
            logger.debug(f"Listening for commands: {', '.join(command_prefixes)}")
            
            logger.debug("Running start events...")
            
            # Runstart events
            events = self.events.get("start", [])
            for event in events:
                await event(self)
            
            logger.debug("Running message loop...")
            
            await self._process_websocket_loop()
            
        except Exception as e:
            logger.exception(f"Failed to start bot: {str(e)}")
    
    async def _process_websocket_loop(self):
        """Process websocket events in a loop"""
        while True:
            try:
                recieved = await self.connection_state.websocket.recv()
                if type(recieved) != str:
                    raise TypeError("The object recieved in the WebSocket was a binary object and not in text form!")
                recieved = json.loads(recieved)
                match recieved["event"]:
                    case "message":
                        await self._process_message_raw(recieved["payload"]["message"])
                    case "phx_reply":
                        pass
                    case _:
                        logger.warning(f"Websocket event {recieved["event"]} not handled!")
                        print(recieved)
                
                await asyncio.sleep(0) # Let other tasks run
            
            except ConnectionClosed as e:
                await asyncio.sleep(5)
                await self._try_reconnect()
                
            except Exception as e:
                logger.exception(f"Error fetching messages: {str(e)}")
                await asyncio.sleep(0) # Let other tasks run
    
    async def _process_message_raw(self, message: dict):
        msg_user = MessageUser(message["user"]["id"], message["user"]["username"], message["user"]["is_bot"], message["user"].get("photo_url", None)).attach_state(self.connection_state)
        msg_flock = PartialFlock(message["flock_id"]).attach_state(self.connection_state)
        msg_nest = PartialNest(message["nest_id"], msg_flock).attach_state(self.connection_state)
        
        message = Message(message["id"], message["content"], msg_flock, msg_nest, datetime.strptime(message["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc), msg_user).attach_state(self.connection_state)
        
        # Run on_message_raw events
        events = self.events.get("on_message_raw", [])
        for event in events:
            await event(message)
            
        # Skip bot messages
        if message.user.is_bot:
            return
        
        logger.debug(f"Message from {message.user.username} in {message.flock.id}/{message.nest.id}: {message.content}")
        
        # Check for commands
        was_command = await self._handle_command(message)
        
        # If it was a command, skip
        if was_command:
            return
        
        # Run on_message events
        events = self.events.get("on_message", [])
        for event in events:
            await event(message)
        
    async def _try_reconnect(self):
        """Try to reconnect the WebSocket."""
        while True:
            try:
                websocket = await connect(self.auth_details["websocket"]["url"])
                await websocket.send(json.dumps(
                    {
                        "topic": self.auth_details["websocket"]["channel"],
                        "event": "phx_join",
                        "payload": {"token": self.token},
                        "ref": "_py_reconnect_attempt"
                    }
                )) 
                recieve_success = await websocket.recv()
                recieved = json.loads(recieve_success)
                if recieved["ref"] == "_py_reconnect_attempt":
                    self.connection_state.websocket = websocket
                    logger.info("Reconnected to WebSocket.")
                    break
            except Exception:
                pass
            await asyncio.sleep(5)
    
    async def _keepalive(self):
        """Keeps the WebSocket alive."""
        while True:
            try:
                await self.connection_state.websocket.send(json.dumps({
                    "topic": "phoenix",
                    "event": "heartbeat",
                    "payload": {},
                    "ref": f"_py_keepalive_{self.ws_keepalive_id}"
                }))
                logger.debug(f"Keepalive #{self.ws_keepalive_id} sent.")
                self.ws_keepalive_id += 1
                # Wait 30 seconds before the next keepalive
                await asyncio.sleep(30)
            except ConnectionClosed:
                pass # should reconnect soon
    
    async def _handle_command(self, message: Message) -> bool:
        """
        Handle command messages
        
        Args:
            message: Message object
        """
        message_content: str = message.content.lower()
        # Check each command prefix
        for prefix, handler in self.commands.items():
            if message_content.startswith(prefix.lower()):
                args = message.content.replace(prefix, "", 1)
                if args != "" and not args[0].isspace():
                    continue # We don't say there's a command to be ran if there's no space between the command name and args 
                logger.debug(f"Command detected: {prefix}")
                
                # Generate response using the command handler, if we don't get an error
                try:
                    args = await parse_args(handler, args.strip(), message, self.connection_state)
                    response_content = await handler(*args)
                except Exception as e:
                    logger.exception(e)
                    events = self.events.get("on_command_exception", [])
                    for event in events:
                        await event(prefix, message, e)
                    return True # a command did run, it just errored
                    
                # Send the response
                # TODO: use the nest object when it has a send() func
                await message.nest.send(response_content)
                
                # Return true after first matching command
                return True
        # No commands were ran, so return false (we didn't run a command)
        return False
    
    @deprecated("use nest.send()")
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
    
    async def get_flocks(self) -> list[Flock]:
        """Get all flocks your bot is in."""
        return await Flock._get_all(self.connection_state)
    
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
        await self.connection_state.websocket.close(1000, "Bot shutting down")
        try:
            asyncio.get_running_loop().stop()
        except RuntimeError:
            pass
        sys.exit(0)