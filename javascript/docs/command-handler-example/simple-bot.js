import { Client } from "../../sdk/corvy.js";
import path from "path";
import fs from "fs";

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

const commandPath = path.resolve("./commands");
const commandFiles = fs.readdirSync(commandPath).filter((file) => file.endsWith(".js"));
for (let file of commandFiles) {
  const command = await import(`./commands/${file}`);

  client.registerCommand([command.name, ...(command.aliases ?? [])], command.execute);
}

client.login();