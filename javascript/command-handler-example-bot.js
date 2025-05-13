import { Client } from "./corvy-sdk.js";
import path from "path";
import fs from "fs";

const client = new Client({
    token: "your_token",
    prefix: ";", // default value
    devMode: true // default value
});

client.on("error", (err) => {
    console.error(err);
});

client.on("ready", (client) => {
    console.log(`${client.user.name} is now online!`);
});

const commandPath = path.resolve("./commands");
const commandFiles = fs.readdirSync(commandPath).filter((file) => file.endsWith(".js"));
for (let file of commandFiles) {
    const command = await import(`./commands/${file}`);
    
    client.registerCommand([command.name, ...(command.aliases ?? [])], command.execute);
}

client.login();
