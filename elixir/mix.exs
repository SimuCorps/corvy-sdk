defmodule CorvyBot.MixProject do
  use Mix.Project

  def project do
    [
      app: :corvy_bot,
      version: "1.0.0",
      elixir: "~> 1.14",
      start_permanent: Mix.env() == :prod,
      deps: deps()
    ]
  end

  defp deps do
    [
      {:httpoison, "~> 2.0"},
      {:jason, "~> 1.4"}
    ]
  end
end 