import { EventEmitter } from "events";

export interface ClientOptions {
    token: string;
    globalPrefix?: string;
    apiBaseUrl?: string;
    apiPath?: string;
}

export interface Message {
    content: string;
    flock_id: string;
    nest_id: string;
    user: {
        id: string;
        username: string;
        is_bot: boolean;
        photo_url: string;
        badge: string;
        available_badges: Array;
    };
    flock_name?: string;
    nest_name?: string;
}

export interface User {
    user: {
        id: string;
        username: string;
        is_bot: boolean;
        photo_url: string;
        badge: string;
        available_badges: string[];
    };
}

export interface Flock {
    flock: {
        id: string;
        name: string;
        icon: string;
        members_count: number;
        nests_count: number;
        created_at: string;
    };
}

export class Client extends EventEmitter {
    /**
     * 
     * @param {Object} options - Bot configuration
     * @param {string} options.token - Authentication token
     * @param {string} [options.prefix=";"] - Global command prefix (default is ";")
     * @param {boolean} options.devMode - Enables more detailed logging
     */
    constructor(options: ClientOptions);

    token: string;
    prefix: string;
    client: any;
    devMode: boolean;

    /**
     * Registers a command
     * @param {string} name - Command name
     * @param {Function} handler - Function to handle the command
     */
    registerCommand(name: string, handler: (msg: Message, client: Client, args: string) => void): void;

    /**
     * Begins login
     */
    login(): Promise<void>;

    /**
     * Sends a message to the specified flock and nest
     * @param {string} flockId - ID of the flock (server)
     * @param {string} nestId - ID of the nest (channel)
     * @param {string} content - Message to send
     */
    sendMsg(flockId: string, nestId: string, content: string): Promise<void>;

    /**
     * Fetches a user object by their ID
     * @param {string} userId - The user ID to look up
     */
    getUserById(userId: string): Promise<User>;

    /**
     * Fetches a user object by their username
     * @param {string} username - The username to look up
     */
    getUserByUsername(username: string): Promise<User>;

    /**
     * Fetches a flock object by its ID
     * @param {string} flockId - The flock ID to look up
     */
    getFlockById(flockId: string): Promise<Flock>;

    on(event: "ready", listener: (client: Client) => void): this;
    on(event: "messageRaw", listener: (msg: Message) => void): this;
    on(event: "message", listener: (msg: Message) => void): this;
    on(event: "error", listener: (err: Error) => void): this;
    on(event: "commandError", listener: (name: string, msg: Message, err: Error) => void): this;
}
