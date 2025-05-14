defmodule CorvyBot.SDK do
  @moduledoc """
  CorvyBot SDK - v1.0.0
  Client library for building Corvy bots
  """

  use GenServer
  require Logger

  defstruct [:config, :current_cursor]

  @doc """
  Creates a new bot instance.
  """
  def start_link(config) do
    GenServer.start_link(__MODULE__, config, name: __MODULE__)
  end

  @impl true
  def init(config) do
    Process.flag(:trap_exit, true)
    # Schedule the start message to be sent after initialization
    Process.send_after(self(), :start, 100)
    {:ok, %__MODULE__{config: config, current_cursor: 0}}
  end

  @impl true
  def handle_info(:start, state) do
    Logger.info("Starting bot...")

    with {:ok, auth_response} <- make_request(:post, "/auth", state.config),
         {:ok, baseline_response} <- make_request(:get, "/messages", state.config, %{cursor: 0}) do
      
      Logger.info("Bot authenticated: #{auth_response["bot"]["name"]}")
      
      cursor = baseline_response["cursor"] || 0
      Logger.info("Baseline established. Starting with message ID: #{cursor}")

      command_prefixes = Enum.map(state.config.commands, & &1.prefix)
      Logger.info("Listening for commands: #{Enum.join(command_prefixes, ", ")}")

      schedule_message_check()
      {:noreply, %{state | current_cursor: cursor}}
    else
      error ->
        Logger.error("Failed to start bot: #{inspect(error)}")
        {:stop, :startup_error, state}
    end
  end

  @impl true
  def handle_info(:check_messages, state) do
    case make_request(:get, "/messages", state.config, %{cursor: state.current_cursor}) do
      {:ok, response} ->
        new_cursor = response["cursor"] || state.current_cursor
        
        response["messages"]
        |> Enum.reject(&(&1["user"] && &1["user"]["is_bot"]))
        |> Enum.each(&handle_command(&1, state.config))

        schedule_message_check()
        {:noreply, %{state | current_cursor: new_cursor}}

      {:error, error} ->
        Logger.error("Error fetching messages: #{inspect(error)}")
        schedule_message_check(5000)
        {:noreply, state}
    end
  end

  @impl true
  def handle_info({:EXIT, _pid, reason}, state) do
    Logger.info("Bot shutting down...")
    {:stop, reason, state}
  end

  defp schedule_message_check(delay \\ 1000) do
    Process.send_after(self(), :check_messages, delay)
  end

  defp handle_command(message, config) do
    Logger.info("Message from #{message["user"]["username"]} in #{message["flock_name"]}/#{message["nest_name"]}: #{message["content"]}")

    Enum.find_value(config.commands, fn command ->
      if String.contains?(String.downcase(message["content"]), String.downcase(command.prefix)) do
        Logger.info("Command detected: #{command.prefix}")
        response_content = command.handler.(message)
        send_response(message["flock_id"], message["nest_id"], response_content, config)
        true
      end
    end)
  end

  defp send_response(flock_id, nest_id, content, config) do
    Logger.info("Sending response: \"#{content}\"")
    make_request(:post, "/flocks/#{flock_id}/nests/#{nest_id}/messages", config, nil, %{content: content})
  end

  defp make_request(method, path, config, params \\ nil, body \\ nil) do
    url = "#{config.api_base_url}#{path}"
    headers = [
      {"Authorization", "Bearer #{config.api_token}"},
      {"Content-Type", "application/json"}
    ]

    options = [ssl: [{:verify, :verify_peer}]]

    case method do
      :get ->
        url = if params, do: "#{url}?#{URI.encode_query(params)}", else: url
        HTTPoison.get(url, headers, options)

      :post ->
        body_json = if body, do: Jason.encode!(body), else: "{}"
        HTTPoison.post(url, body_json, headers, options)

      :put ->
        body_json = if body, do: Jason.encode!(body), else: "{}"
        HTTPoison.put(url, body_json, headers, options)

      :delete ->
        HTTPoison.delete(url, headers, options)

      _ ->
        {:error, "Unsupported HTTP method: #{method}"}
    end
    |> case do
      {:ok, %{status_code: status, body: body}} when status >= 200 and status < 300 ->
        {:ok, Jason.decode!(body)}

      {:ok, %{status_code: status, body: body}} ->
        {:error, "HTTP Error #{status}: #{body}"}

      {:error, %{reason: reason}} ->
        {:error, reason}
    end
  end
end 