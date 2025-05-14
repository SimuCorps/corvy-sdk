import { Client } from "../sdk/corvy.js";

const client = new Client({
  token: "your_token",
  prefix: ";", // default value
  devMode: true, // default value (true = more detailed logging)
});

client.on("error", (err) => {
  console.error(err);
});

client.on("ready", (client) => {
  console.log(`${client.user.name} is now online!`);
  console.log(`I am in ${client.flocks.size} flocks.`);
});

client.registerCommand("ping", async (msg, client, args) => {
  return "Pong!";
});

client.login();