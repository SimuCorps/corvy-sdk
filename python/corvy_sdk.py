# CorvyBot SDK - v1.0.0
# Client library for building Corvy bots

import requests
import json
import time
import signal
import sys
from typing import List, Dict, Callable, Any, Optional, Union

class CorvyBot:
    """
    Client library for building Corvy bots
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Create a new bot instance
        
        Args:
            config: Bot configuration with apiToken, apiBaseUrl, and commands
        """
        self.config = config
        self.current_cursor = 0
        self.headers = {
            'Authorization': f"Bearer {self.config['apiToken']}",
            'Content-Type': 'application/json'
        }
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        
    def start(self):
        """Start the bot and begin processing messages"""
        try:
            print("Starting bot...")
            
            # Authenticate first
            response = requests.post(
                f"{self.config['apiBaseUrl']}/auth",
                headers=self.headers
            )
            response.raise_for_status()
            response_data = response.json()
            print(f"Bot authenticated: {response_data['bot']['name']}")
            
            # Establish baseline (gets highest message ID but no messages)
            print("Establishing baseline with server...")
            baseline_response = requests.get(
                f"{self.config['apiBaseUrl']}/messages",
                params={'cursor': 0},
                headers=self.headers
            )
            baseline_response.raise_for_status()
            baseline_data = baseline_response.json()
            
            # Save the cursor for future requests
            if baseline_data.get('cursor'):
                self.current_cursor = baseline_data['cursor']
                print(f"Baseline established. Starting with message ID: {self.current_cursor}")
            
            # Log command prefixes
            command_prefixes = [cmd['prefix'] for cmd in self.config['commands']]
            print(f"Listening for commands: {', '.join(command_prefixes)}")
            
            # Start processing messages
            self._process_message_loop()
            
        except Exception as e:
            print(f"Failed to start bot: {str(e)}")
            sys.exit(1)
            
    def _process_message_loop(self):
        """Process messages in a loop"""
        while True:
            try:
                # Get new messages
                response = requests.get(
                    f"{self.config['apiBaseUrl']}/messages",
                    params={'cursor': self.current_cursor},
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                
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
                    self._handle_command(message)
                
                # Wait before checking again
                time.sleep(1)
                
            except Exception as e:
                print(f"Error fetching messages: {str(e)}")
                time.sleep(5)  # Longer delay on error
                
    def _handle_command(self, message: Dict[str, Any]):
        """
        Handle command messages
        
        Args:
            message: Message object
        """
        # Check each command prefix
        for command in self.config['commands']:
            if command['prefix'].lower() in message['content'].lower():
                print(f"Command detected: {command['prefix']}")
                
                # Generate response using the command handler
                response_content = command['handler'](message)
                
                # Send the response
                self._send_response(message['flock_id'], message['nest_id'], response_content)
                
                # Stop after first matching command
                break
                
    def _send_response(self, flock_id: Union[str, int], nest_id: Union[str, int], content: str):
        """
        Send a response message
        
        Args:
            flock_id: Flock ID
            nest_id: Nest ID
            content: Message content
        """
        try:
            print(f'Sending response: "{content}"')
            
            response = requests.post(
                f"{self.config['apiBaseUrl']}/flocks/{flock_id}/nests/{nest_id}/messages",
                json={'content': content},
                headers=self.headers
            )
            response.raise_for_status()
            
        except Exception as e:
            print(f"Failed to send response: {str(e)}")
            
    def _handle_shutdown(self, sig, frame):
        """Handle graceful shutdown"""
        print("Bot shutting down...")
        sys.exit(0) 