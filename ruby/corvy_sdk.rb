# CorvyBot SDK - v1.0.0
# Client library for building Corvy bots

require 'net/http'
require 'uri'
require 'json'

class CorvyBot
  # Create a new bot instance
  # @param config [Hash] Bot configuration with apiToken, apiBaseUrl, and commands
  def initialize(config)
    @config = config
    @current_cursor = 0
    
    # Set up signal handlers for graceful shutdown
    Signal.trap("INT") { shutdown }
  end
  
  # Start the bot and begin processing messages
  def start
    begin
      puts "Starting bot..."
      
      # Authenticate first
      auth_response = make_request(:post, "/auth")
      puts "Bot authenticated: #{auth_response["bot"]["name"]}"
      
      # Establish baseline (gets highest message ID but no messages)
      puts "Establishing baseline with server..."
      baseline_response = make_request(:get, "/messages", cursor: 0)
      
      # Save the cursor for future requests
      if baseline_response["cursor"]
        @current_cursor = baseline_response["cursor"]
        puts "Baseline established. Starting with message ID: #{@current_cursor}"
      end
      
      # Log command prefixes
      command_prefixes = @config[:commands].map { |cmd| cmd[:prefix] }
      puts "Listening for commands: #{command_prefixes.join(", ")}"
      
      # Start processing messages
      process_message_loop
      
    rescue => e
      puts "Failed to start bot: #{e.message}"
      exit(1)
    end
  end
  
  private
  
  # Process messages in a loop
  def process_message_loop
    loop do
      begin
        # Get new messages
        response = make_request(:get, "/messages", cursor: @current_cursor)
        
        # Update cursor
        @current_cursor = response["cursor"] if response["cursor"]
        
        # Process each new message
        response["messages"]&.each do |message|
          # Skip bot messages
          next if message["user"] && message["user"]["is_bot"]
          
          puts "Message from #{message["user"]["username"]} in #{message["flock_name"]}/#{message["nest_name"]}: #{message["content"]}"
          
          # Check for commands
          handle_command(message)
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
  # @param message [Hash] Message object
  def handle_command(message)
    # Check each command prefix
    @config[:commands].each do |command|
      if message["content"].downcase.include?(command[:prefix].downcase)
        puts "Command detected: #{command[:prefix]}"
        
        # Generate response using the command handler
        response_content = command[:handler].call(message)
        
        # Send the response
        send_response(message["flock_id"], message["nest_id"], response_content)
        
        # Stop after first matching command
        break
      end
    end
  end
  
  # Send a response message
  # @param flock_id [String, Integer] Flock ID
  # @param nest_id [String, Integer] Nest ID
  # @param content [String] Message content
  def send_response(flock_id, nest_id, content)
    begin
      puts "Sending response: \"#{content}\""
      
      make_request(:post, "/flocks/#{flock_id}/nests/#{nest_id}/messages", nil, content: content)
      
    rescue => e
      puts "Failed to send response: #{e.message}"
    end
  end
  
  # Make an HTTP request to the Corvy API
  # @param method [Symbol] HTTP method (:get, :post, etc.)
  # @param path [String] API endpoint path
  # @param params [Hash] Query parameters
  # @param body [Hash] Request body
  # @return [Hash] Parsed JSON response
  def make_request(method, path, params = nil, body = nil)
    uri = URI.parse("#{@config[:apiBaseUrl]}#{path}")
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
    
    request["Authorization"] = "Bearer #{@config[:apiToken]}"
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