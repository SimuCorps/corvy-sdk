import { Client } from "./sdk/corvy.js";

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

client.registerCommand("ping", async (msg, client, args) => {
    return await client.sendMsg(msg.flock_id, msg.nest_id, "Pong!");
});

client.login();
