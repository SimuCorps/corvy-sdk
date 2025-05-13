export const name = "ping";
export const aliases = ["p"]; // not required at all. you do not need this if you don't want it.

export async function execute(msg, client, args) {
    return await client.sendMsg(msg.flock_id, msg.nest_id, "Pong...");
}
