import axios from "axios";
import EventEmitter from "events";

export class Client extends EventEmitter {
  constructor({ token, prefix = ";", devMode = false }) {
    super();
    this.token = token;
    this.prefix = prefix;
    this.currentCursor = 0;
    this.commands = new Map();
    this.user = null;
    this.devMode = devMode;
    this.client = axios.create({
      baseURL: "https://corvy.chat/api/v1",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json"
      }
    });
  }

  // -------------------------------
  // Utils
  // -------------------------------

  log(...args) {
    if (this.devMode) {
      console.log("[DEV MODE]", ...args);
    }
  }
  
  // -------------------------------
  // Command Registration
  // -------------------------------

  registerCommand(names, handler) {
    const nameList = Array.isArray(names) ? names : [names];

    for (let name of nameList) {
      if (typeof name !== "string" || typeof handler !== "function") {
        throw new Error("Command must be registered with a name and a function handler.");
      }

      const fullPrefix = `${this.prefix}${name}`;
      this.commands.set(fullPrefix.toLowerCase(), async (msg, client, argsText) => {
        try {
          this.log(`Executing command: ${fullPrefix}`);
          this.log(`Executing command: ${fullPrefix}`);
          const data = await handler(msg, client, argsText);
          if (data) {
            await client.sendMsg(msg.flock_id, msg.nest_id, data);
          }
        } catch (err) {
          this.emit("commandError", fullPrefix, msg, err);
          this.log(`Error in command "${fullPrefix}": ${err.message}`);
        }
      });

      this.log(`Registered command: ${fullPrefix}`);
    }
  }

  // -------------------------------
  // Auth
  // -------------------------------

  async login() {
    try {

      const res = await this.client.post("/auth");
      this.user = res.data.bot;

      this.emit("ready", this);

      const baseline = await this.client.get("/messages", {
        params: { cursor: 0 }
      });

      this.currentCursor = baseline.data.cursor || 0;

      this.processMessages();

      process.on("SIGINT", () => {
        console.log("Client shutting down...");
        process.exit(0);
      });
    } catch (err) {
      this.emit("error", new Error("Error logging in: " + err.message));
      this.log(`Error logging in: ${err.message}`);
    }
  }

  // -------------------------------
  // Message Loop
  // -------------------------------

  async processMessages() {
    this.log("Starting message loop...");

    while (true) {
      try {
        const res = await this.client.get("/messages", {
          params: { cursor: this.currentCursor }
        });

        const data = res.data;
        if (data.cursor) {
          this.currentCursor = data.cursor;
        }

        for (const msg of data.messages || []) {
          if (msg.user.is_bot) {
            continue;
          }

          this.emit("messageRaw", msg);
          this.log(`Received message "${msg.content}" from "${msg.user.username}" in "${msg.flock_name}/${msg.nest_name}"`);

          const handled = await this.handleCommand(msg);
          if (!handled) {
            this.emit("message", msg);
          }
        }

        await new Promise(r => setTimeout(r, 1000));
      } catch (err) {
        this.emit("error", new Error("Error in message loop: " + err.message));
        this.log(`Error in message loop: ${err.message}`);
        await new Promise(r => setTimeout(r, 5000));
      }
    }
  }

  async handleCommand(msg) {
    const content = msg.content.toLowerCase();
    for (const [prefix, handler] of this.commands.entries()) {
      if (content.startsWith(prefix)) {
        const argsText = msg.content.slice(prefix.length).trim();
        await handler(msg, this, argsText);

        return true;
      }
    }

    return false;
  }

  // -------------------------------
  // API Helpers
  // -------------------------------

  async sendMsg(flockId, nestId, content) {
    try {
      this.log(`Sending message to flock:${flockId}, nest:${nestId} -> "${content}"`);
      await this.client.post(`/flocks/${flockId}/nests/${nestId}/messages`, { content });
    } catch (err) {
      this.emit("error", new Error("Send message failed: " + err.message));
      this.log(`Send message failed: ${err.message}`);
    }
  }

  async getUserById(userId) {
    try {
      this.log(`Fetching user by ID: ${userId}`);
      const response = await this.client.get(`/users/${userId}`);
      return response.data;
    } catch (err) {
      this.emit("error", new Error("Get user by id failed: " + err.message));
      this.log(`Get user by id failed: ${err.message}`);
    }
  }

  async getUserByUsername(username) {
    try {
      this.log(`Fetching user by username: ${username}`);
      const response = await this.client.get(`/users/by-username/${username}`);

      return response.data;
    } catch (err) {
      this.emit("error", new Error("Get user by username failed: " + err.message));
      this.log(`Get user by username failed: ${err.message}`);
    }
  }

  async getFlockById(flockId) {
    try {
      this.log(`Fetching flock by id: ${flockId}`);
      const response = await this.client.get(`/flocks/${flockId}`);

      return response.data;
    } catch (err) {
      this.emit("error", new Error("Get flock by id failed: " + err.message));
      this.log(`Get flock by id failed: ${err.message}`);
    }
  }
};
