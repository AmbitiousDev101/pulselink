type MessageCallback = (data: unknown) => void;

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export let WS_URL = API_URL;
if (WS_URL.startsWith("https://")) {
  WS_URL = WS_URL.replace(/^https:\/\//, "wss://");
} else if (WS_URL.startsWith("http://")) {
  WS_URL = WS_URL.replace(/^http:\/\//, "ws://");
}

class WebSocketManager {
  private ws: WebSocket | null = null;
  private callbacks: MessageCallback[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private isConnecting = false;
  private _isConnected = false;

  get isConnected(): boolean {
    return this._isConnected;
  }

  connect(): void {
    if (this.isConnecting || this._isConnected) return;
    if (typeof window === "undefined") return;

    this.isConnecting = true;

    try {
      console.log(`[WS] Attempting to connect to: ${WS_URL}/ws/feed`);
      this.ws = new WebSocket(`${WS_URL}/ws/feed`);

      this.ws.onopen = () => {
        this.isConnecting = false;
        this._isConnected = true;
        this.reconnectAttempts = 0;
        console.log("[WS] Connected to live feed");
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.callbacks.forEach((cb) => cb(data));
        } catch (e) {
          console.error("[WS] Failed to parse message:", e);
        }
      };

      this.ws.onclose = () => {
        this.isConnecting = false;
        this._isConnected = false;
        console.log("[WS] Disconnected");
        this.scheduleReconnect();
      };

      this.ws.onerror = (err) => {
        console.error("[WS] Error:", err);
        this.ws?.close();
      };
    } catch (e) {
      this.isConnecting = false;
      console.error("[WS] Connection failed:", e);
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log("[WS] Max reconnect attempts reached");
      return;
    }

    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;

    console.log(
      `[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`
    );

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.reconnectAttempts = this.maxReconnectAttempts; // prevent reconnect
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this._isConnected = false;
  }

  onMessage(callback: MessageCallback): () => void {
    this.callbacks.push(callback);
    return () => {
      this.callbacks = this.callbacks.filter((cb) => cb !== callback);
    };
  }
}

// Singleton
const wsManager = new WebSocketManager();
export default wsManager;
