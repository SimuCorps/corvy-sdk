# CorvyBot SDK - v1.5.1
# Client library for building Corvy bots

require 'net/http'
require 'uri'
require 'json'
require 'time'
require 'shellwords'

# Type annotation helper for greedy parameters
class Greedy
  # Marker class for greedy parameters
end

# Helper for casting command arguments to the correct type
def cast_type(type, raw)
  case type
  when :string
    raw
  when :integer
    raw.to_i
  when :float
    raw.to_f
  when :boolean
    %w[1 true yes y t].include?(raw.downcase)
  else
    raise "Unsupported type: #{type}"
  end
end

# Parse arguments for a command
def parse_args(command_info, input_str, message)
  # Simple case - just pass message to handler
  return [message] if command_info[:params].empty?
  
  tokens = Shellwords.split(input_str)
  out_args = []
  idx = 0
  message_injected = false
  
  command_info[:params].each_with_index do |param, i|
    # If parameter is a message object
    if param[:type] == :message
      if message_injected
        # Second message not allowed unless it's optional
        if param[:optional]
          out_args << nil
          next
        end
        raise "Multiple Message parameters not allowed: #{param[:name]}"
      end
      out_args << message
      message_injected = true
      next
    end
    
    # Handle greedy parameter
    if param[:greedy]
      needed_for_rest = command_info[:params].length - (i + 1)
      take = [0, tokens.length - idx - needed_for_rest].max
      raw = tokens[idx, take].join(' ')
      idx += take
      out_args << cast_type(param[:type], raw)
      next
    end
    
    # Handle regular parameter
    if idx >= tokens.length
      if param[:default]
        out_args << param[:default]
        next
      end
      if param[:optional]
        out_args << nil
        next
      end
      raise "Missing value for parameter '#{param[:name]}'"
    end
    
    raw = tokens[idx]
    idx += 1
    
    if param[:optional] && raw.downcase == 'none'
      out_args << nil
    else
      out_args << cast_type(param[:type], raw)
    end
  end
  
  out_args
end

# User representation
class MessageUser
  attr_reader :id, :username, :is_bot
  
  def initialize(id, username, is_bot)
    @id = id
    @username = username
    @is_bot = is_bot
  end
end

# Message representation
class Message
  attr_reader :id, :content, :flock_name, :flock_id, :nest_name, :nest_id, :created_at, :user
  
  def initialize(id, content, flock_name, flock_id, nest_name, nest_id, created_at, user)
    @id = id
    @content = content
    @flock_name = flock_name
    @flock_id = flock_id
    @nest_name = nest_name
    @nest_id = nest_id
    @created_at = created_at
    @user = user
  end
end

class CorvyBot
  # Create a new bot instance
  # @param token [String] Token for the Corvy API
  # @param global_prefix [String] The prefix for all commands
  # @param api_base_url [String] The URL for the Corvy API
  # @param api_path [String] API path endpoint
  def initialize(token, global_prefix = "!", api_base_url = "https://corvy.chat", api_path = "/api/v1")
    @commands = {}
    @token = token
    @global_prefix = global_prefix
    @api_base_url = api_base_url
    @api_path = api_path
    @current_cursor = 0
    @events = {}
    
    # Set up signal handlers for graceful shutdown
    Signal.trap("INT") { shutdown }
  end
  
  # Register a command
  # @param prefix [String, nil] The prefix of the command
  # @return [Proc] Decorator function to register the command
  def command(prefix = nil)
    lambda do |func|
      command_name = prefix || "#{@global_prefix}#{func.name}"
      params = []
      
      # Extract parameter info from method definition if possible
      method_params = func.parameters
      method_params.each do |param_type, param_name|
        # Simple mapping for demonstration
        param_info = {
          name: param_name,
          type: :string,
          optional: param_type == :opt || param_type == :key,
          greedy: false,
          default: nil
        }
        
        # Special case for message parameter
        if param_name.to_s == 'message'
          param_info[:type] = :message
        end
        
        params << param_info
      end
      
      @commands[command_name] = {
        handler: func,
        params: params
      }
      
      func
    end
  end
  
  # Register an event handler
  # @param event [String, nil] The event to register for
  # @return [Proc] Decorator function to register the event
  def event(event = nil)
    lambda do |func|
      event_name = event || func.name
      @events[event_name] ||= []
      @events[event_name] << func
      func
    end
  end
  
  # Start the bot and begin processing messages
  def start
    begin
      puts "Starting bot..."
      
      # Authenticate first
      auth_response = make_request(:post, "#{@api_path}/auth")
      puts "Bot authenticated: #{auth_response["bot"]["name"]}"
      
      # Establish baseline (gets highest message ID but no messages)
      puts "Establishing baseline with server..."
      baseline_response = make_request(:get, "#{@api_path}/messages", cursor: 0)
      
      # Save the cursor for future requests
      if baseline_response["cursor"]
        @current_cursor = baseline_response["cursor"]
        puts "Baseline established. Starting with message ID: #{@current_cursor}"
      end
      
      # Log command prefixes
      command_prefixes = @commands.keys
      puts "Listening for commands: #{command_prefixes.join(", ")}"
      
      # Start processing messages
      process_message_loop
      
    rescue => e
      puts "Failed to start bot: #{e.message}"
      exit(1)
    end
  end
  
  # Send a message
  # @param flock_id [String, Integer] Flock ID
  # @param nest_id [String, Integer] Nest ID
  # @param content [String] Message content
  def send_message(flock_id, nest_id, content)
    begin
      puts "Sending message: \"#{content}\""
      
      make_request(:post, "#{@api_path}/flocks/#{flock_id}/nests/#{nest_id}/messages", nil, content: content)
      
    rescue => e
      puts "Failed to send message: #{e.message}"
    end
  end
  
  private
  
  # Process messages in a loop
  def process_message_loop
    loop do
      begin
        # Get new messages
        response = make_request(:get, "#{@api_path}/messages", cursor: @current_cursor)
        
        # Update cursor
        @current_cursor = response["cursor"] if response["cursor"]
        
        # Process each new message
        response["messages"]&.each do |msg|
          # Convert to Message object
          user = MessageUser.new(
            msg["user"]["id"],
            msg["user"]["username"],
            msg["user"]["is_bot"]
          )
          
          message = Message.new(
            msg["id"],
            msg["content"],
            msg["flock_name"],
            msg["flock_id"],
            msg["nest_name"],
            msg["nest_id"],
            Time.parse(msg["created_at"]),
            user
          )
          
          # Run on_message_raw events
          if @events["on_message_raw"]
            @events["on_message_raw"].each do |event_handler|
              event_handler.call(message)
            end
          end
          
          # Skip bot messages
          next if message.user.is_bot
          
          puts "Message from #{message.user.username} in #{message.flock_name}/#{message.nest_name}: #{message.content}"
          
          # Check for commands
          was_command = handle_command(message)
          
          # If it was a command, skip
          next if was_command
          
          # Run on_message events
          if @events["on_message"]
            @events["on_message"].each do |event_handler|
              event_handler.call(message)
            end
          end
        end
        
        # Wait before checking again
        sleep(1)
        
      rescue => e
        puts "Error fetching messages: #{e.message}"
        sleep(5) # Longer delay on error
      end
    end
  end
  
  # Handle command messages
  # @param message [Message] Message object
  # @return [Boolean] Whether a command was handled
  def handle_command(message)
    message_content = message.content.downcase
    
    # Check each command prefix
    @commands.each do |prefix, command_info|
      if message_content.start_with?(prefix.downcase)
        puts "Command detected: #{prefix}"
        
        begin
          # Parse arguments and call handler
          args = parse_args(
            command_info,
            message.content.sub(prefix, "").strip,
            message
          )
          
          response_content = command_info[:handler].call(*args)
          
          # Send the response
          send_message(message.flock_id, message.nest_id, response_content)
          
          # Return true to indicate command was handled
          return true
        rescue => e
          # Run on_command_exception events if available
          if @events["on_command_exception"]
            @events["on_command_exception"].each do |event_handler|
              event_handler.call(prefix, message, e)
            end
          end
          return false
        end
      end
    end
    
    # No commands were handled
    false
  end
  
  # Make an HTTP request to the Corvy API
  # @param method [Symbol] HTTP method (:get, :post, etc.)
  # @param path [String] API endpoint path
  # @param params [Hash] Query parameters
  # @param body [Hash] Request body
  # @return [Hash] Parsed JSON response
  def make_request(method, path, params = nil, body = nil)
    uri = URI.parse("#{@api_base_url}#{path}")
    uri.query = URI.encode_www_form(params) if params
    
    http = Net::HTTP.new(uri.host, uri.port)
    http.use_ssl = uri.scheme == 'https'
    
    request = case method
      when :get then Net::HTTP::Get.new(uri)
      when :post then Net::HTTP::Post.new(uri)
      when :put then Net::HTTP::Put.new(uri)
      when :delete then Net::HTTP::Delete.new(uri)
      else raise "Unsupported HTTP method: #{method}"
    end
    
    request["Authorization"] = "Bearer #{@token}"
    request["Content-Type"] = 'application/json'
    request.body = body.to_json if body
    
    response = http.request(request)
    
    if response.code.to_i >= 200 && response.code.to_i < 300
      JSON.parse(response.body)
    else
      raise "HTTP Error #{response.code}: #{response.body}"
    end
  end
  
  # Handle graceful shutdown
  def shutdown
    puts "Bot shutting down..."
    exit(0)
  end
end 