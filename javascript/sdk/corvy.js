import WebSocket from 'ws';
import axios from 'axios';
import { EventEmitter } from 'events';
import { Socket } from 'phoenix';

export default class Client extends EventEmitter {
    constructor({ prefix = '!', token, devMode = false, help = false }) {
        super();
        this.prefix = prefix;
        this.token = token;
        this.devMode = devMode;
        this.help = help;
        this.flockNestMap = {};
        this.socket = null;
        this.channel = null;
        this.commands = new Map();
        this.startTime = Date.now();

        this.API_BASE_URL = 'https://corvy.chat/api/v2';
        this.WEBSOCKET_URL = 'wss://corvy.chat/api/v2/socket';

        this.axiosInstance = axios.create({
            baseURL: this.API_BASE_URL,
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        process.nextTick(async () => {
            await this._initialize();

            if (this.help) {
                const helpMessage = this._generateHelpMessage().join('<br />');
                this.registerCommand('help', async () => helpMessage);
            }
        });
    }

    _generateHelpMessage() {
        const commands = Array.from(this.commands);
        const commandSet = commands.map(([name, data]) => ({
            name,
            desc: data.desc || "No description provided."
        })).filter(cmd => !cmd.hide);

        const maxNameLength = Math.max(...commandSet.map(cmd => (this.prefix + cmd.name).length));

        const commandsMessage = commandSet.map(cmd => {
            const paddedName = (this.prefix + cmd.name).padEnd(maxNameLength, ' ');
            return `• ${paddedName} → ${cmd.desc}`;
        });

        return [`📜 **Command List**`, ...commandsMessage]
    }


    _log(message) {
        if (this.devMode) {
            console.log(`[DEBUG] ${message}`);
        }
    }

    async _initialize() {
        try {
            const response = await this.axiosInstance.post(`${this.API_BASE_URL}/auth`);

            this.bot = response.data.bot;
        }
        catch (ex) {
            console.log(ex)
        }

        await this._connectSocket();
        this._setupProcessHandlers();
    }

    async _connectSocket() {
        this.socket = new Socket(this.WEBSOCKET_URL, {
            params: { token: this.token },
            heartbeatIntervalMs: 25000,
            transport: WebSocket
        });

        this.socket.connect();

        this.socket.onOpen(() => {
            this._log('✅ Socket connection established');
            this.emit('ready', this.bot);
        });
        this.socket.onError((error) => {
            this._log(`❌ Socket error: ${error.message}`);
            this.emit('error', new Error(`Socket error: ${error.message}`));
        });
        this.socket.onClose((event) => this._log(`Socket connection closed: ${event.code} - ${event.reason}`));

        this._joinBotChannel();
    }

    _joinBotChannel() {
        this.channel = this.socket.channel("bot:any", { token: this.token });

        this.channel.on("message", (payload) => {
            if (payload.event === 'new_message') {
                this._handleNewMessage(payload.message);
            }
        });

        this.channel.join()
            .receive("ok", (response) => {
                this._log('✅ Successfully joined bot channel');
            })
            .receive("error", (response) => {
                this._log(`❌ Failed to join bot channel: ${JSON.stringify(response)}`);
                this.emit('error', new Error(`Failed to join bot channel: ${JSON.stringify(response)}`));
            });
    }

    _setupProcessHandlers() {
        process.on('SIGINT', () => {
            this._log('\nShutting down...');
            if (this.socket) {
                this.socket.disconnect();
            }
            process.exit(0);
        });
    }

    checkForStaff(userid, staffs) {
        return staffs?.includes(userid)
    }

    registerCommand(data, handler) {
        const names = data.names ?? data
        const desc = data.desc
        const staffUserIds = data.staff
        if (!handler || typeof handler !== 'function') {
            throw new Error('Command handler must be a function');
        }

        const nameList = Array.isArray(names) ? names : [names];

        for (const name of nameList) {
            if (typeof name !== 'string' || name.trim() === '') {
                throw new Error('Command name must be a non-empty string');
            }

            const normalizedName = name.toLowerCase().trim();
            this._log(`📝 Registered command: ${this.prefix}${normalizedName}`);

            this.commands.set(normalizedName, {
                staff: staffUserIds,
                desc: desc,
                hide: data.hide,
                callback: async (msg, client, args) => {
                    try {
                        const allowedStaff = Array.isArray(staffUserIds) ? staffUserIds : [];

                        const isStaff = allowedStaff.length === 0 || this.checkForStaff(msg.user.id, allowedStaff);
                        if (!isStaff) {
                            await this.sendMessage(msg.flock_id, msg.nest_id, `🚫 You are not permitted to use the **${this.prefix}${normalizedName}** command.`);
                            return;
                        }

                        this._log(`📣 Executing command: ${this.prefix}${normalizedName}`);

                        const response = await handler(msg, client, args);
                        if (response) {
                            await this.sendMessage(msg.flock_id, msg.nest_id, response);
                        }
                    } catch (error) {
                        this._log(`❌ Error in command "${normalizedName}": ${error.message}`);
                        this.emit('commandError', normalizedName, msg, error);
                    }
                }
            });

        }
    }

    sendMessage(flockId, nestId, content) {
        this.channel.push("send_message", {
            flock_id: flockId.toString(),
            nest_id: nestId.toString(),
            content: content
        })
            .receive("ok", () => {
                this._log(`📤 Sent message to nest ${nestId} in flock ${flockId}`);
            })
            .receive("error", (response) => {
                this._log(`❌ Failed to send message: ${JSON.stringify(response)}`);
                this.emit('error', new Error(`Failed to send message: ${JSON.stringify(response)}`));
            });
    }

    async _handleNewMessage(message) {
        const msgContent = message.content;
        const nestId = message.nest_id;
        const flockId = message.flock_id;
        const sender = message.user?.username || 'unknown';

        this.emit('messageRaw', message);

        if (message.user?.is_bot) {
            return;
        }

        if (!msgContent || !nestId) return;

        if (flockId && nestId) {
            this.flockNestMap[nestId.toString()] = flockId.toString();
        }

        this._log(`📨 Message in nest ${nestId} from ${sender}: '${msgContent}'`);

        if (msgContent.startsWith(this.prefix)) {
            const parts = msgContent.slice(this.prefix.length).trim().split(/\s+/);
            const commandName = parts[0].toLowerCase();
            const args = parts.slice(1);
            const argsText = msgContent.slice(this.prefix.length + commandName.length).trim();

            const handled = await this._executeCommand(message, commandName, args, argsText);

            if (!handled) {
                this.emit('message', message);
            }
        } else {
            this.emit('message', message);
        }
    }

    async _executeCommand(message, commandName, args, argsText) {
        const commandHandler = this.commands.get(commandName);

        if (commandHandler) {
            let flockId = message.flock_id

            if (!flockId) {
                flockId = this.flockNestMap[message.nest_id.toString()];

                /* Keeping incase dishy does some API stuff again. */
                // if (!flockId) {
                //     this._log(`⚠️ Could not find flock ID for nest ${message.nest_id}, can't respond`);
                //     return false;
                // }

                message.flock_id = flockId;
            }

            await commandHandler.callback(message, this, args, argsText);
            return true;
        }

        return false;
    }

    async _fetchFlockForNest(nestId) {
        this._log(`🔍 Looking up flock for nest ${nestId}...`);

        try {
            const response = await this.axiosInstance.get(`/flocks`);

            if (response.status === 200 && response.data.success) {
                return await this._checkFlocksForNest([...response.data.flocks], nestId);
            } else {
                this._log(`⚠️ API response unsuccessful when fetching flocks`);
                return null;
            }
        } catch (error) {
            this._log(`⚠️ HTTP error while fetching flocks: ${error.message}`);
            return null;
        }
    }

    async _checkFlocksForNest(flocks, nestId) {
        if (flocks.length === 0) return null;

        const flock = flocks.shift();

        try {
            const response = await this.axiosInstance.get(`/flocks/${flock.id}/nests`);

            if (response.status === 200 && response.data.success) {
                for (const nest of response.data.nests) {
                    if (nest.id.toString() === nestId.toString()) {
                        const flockId = flock.id;
                        this.flockNestMap[nestId.toString()] = flockId;
                        this._log(`✅ Found flock ${flockId} for nest ${nestId}`);
                        return flockId;
                    }
                }
            }

            if (flocks.length > 0) {
                return await this._checkFlocksForNest(flocks, nestId);
            } else {
                this._log(`⚠️ Couldn't find flock ID for nest ${nestId} in any flock`);
                return null;
            }
        } catch (error) {
            this._log(`⚠️ HTTP error while fetching nests for flock ${flock.id}: ${error.message}`);
            if (flocks.length > 0) {
                return await this._checkFlocksForNest(flocks, nestId);
            }
            return null;
        }
    }

    async getUserById(userId) {
        try {
            this._log(`Fetching user by ID: ${userId}`);
            const response = await this.axiosInstance.get(`/users/${userId}`);
            return response.data;
        } catch (err) {
            this.emit("error", new Error("Get user by id failed: " + err.message));
            this._log(`Get user by id failed: ${err.message}`);
        }
    }

    async getUserByUsername(username) {
        try {
            this._log(`Fetching user by username: ${username}`);
            const response = await this.axiosInstance.get(`/users/by-username/${username}`);

            return response.data;
        } catch (err) {
            this.emit("error", new Error("Get user by username failed: " + err.message));
            this._log(`Get user by username failed: ${err.message}`);
        }
    }

    get uptime() {
        return Date.now() - this.startTime;
    }

    get formattedUptime() {
        const ms = this.uptime;
        const sec = Math.floor((ms / 1000) % 60);
        const min = Math.floor((ms / (1000 * 60)) % 60);
        const hr = Math.floor((ms / (1000 * 60 * 60)) % 24);
        const days = Math.floor(ms / (1000 * 60 * 60 * 24));
        const parts = [];

        if (days) parts.push(`${days}d`);
        if (hr) parts.push(`${hr}h`);
        if (min) parts.push(`${min}m`);
        if (sec || parts.length === 0) parts.push(`${sec}s`);

        return parts.join(" ");
    }
}