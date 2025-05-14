defmodule EchoBot do
  @moduledoc """
  CorvyBot Example - Echo Bot
  This bot echoes back any message that includes the command prefix.
  """

  require Logger

  def start do
    # Replace these values with your actual bot token and API URL
    config = %{
      api_token: "your_api_token_here",
      api_base_url: "https://corvy.chat/api/v1",
      commands: [
        %{
          prefix: "!echo",
          handler: fn message ->
            content = message["content"]
            |> String.downcase()
            |> String.split("!echo")
            |> List.last()
            |> String.trim()

            if content == "", do: "You said nothing!", else: "Echo: #{content}"
          end
        },
        %{
          prefix: "!hello",
          handler: fn message ->
            "Hello, #{message["user"]["username"]}! How are you today?"
          end
        },
        %{
          prefix: "!help",
          handler: fn _message ->
            "Available commands: !echo [text], !hello, !help"
          end
        }
      ]
    }

    # Start the SDK directly
    case CorvyBot.SDK.start_link(config) do
      {:ok, pid} ->
        Logger.info("Bot started successfully")
        # Keep the process running
        Process.link(pid)
        :ok
      {:error, reason} ->
        Logger.error("Failed to start bot: #{inspect(reason)}")
        {:error, reason}
    end
  end
end

# Start the bot and keep it running
EchoBot.start()
# Keep the main process alive
Process.sleep(:infinity) 