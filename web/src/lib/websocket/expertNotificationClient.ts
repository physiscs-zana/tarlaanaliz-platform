// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// KR-019: Bildirim kanallari: SMS + web portal ici gercek zamanli bildirim (WebSocket); e-posta kanal degildir.

export interface ExpertNotification {
  readonly reviewId: string;
  readonly type: 'new_review' | 'escalation' | 'sla_warning';
  readonly message: string;
  readonly createdAt: string;
}

type NotificationHandler = (notification: ExpertNotification) => void;

export class ExpertNotificationClient {
  private ws: WebSocket | null = null;
  private handlers: Set<NotificationHandler> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(private readonly wsUrl: string, private readonly token: string) {}

  connect(): void {
    if (typeof window === 'undefined') return;

    try {
      // SEC-FIX: Token is no longer passed as a URL query parameter (visible in
      // server logs, browser history, Referer headers). Instead, it is sent as
      // the first message after the WebSocket connection opens.
      this.ws = new WebSocket(this.wsUrl);

      this.ws.onmessage = (event) => {
        try {
          const notification = JSON.parse(event.data as string) as ExpertNotification;
          for (const handler of this.handlers) {
            handler(notification);
          }
        } catch {
          // Malformed message — ignore
        }
      };

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        // Send auth token as first message so server can authenticate the connection
        this.ws?.send(JSON.stringify({ type: 'auth', token: this.token }));
      };

      this.ws.onclose = () => {
        this.scheduleReconnect();
      };

      this.ws.onerror = () => {
        this.ws?.close();
      };
    } catch {
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;
    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectTimer = setTimeout(() => this.connect(), delay);
  }

  subscribe(handler: NotificationHandler): () => void {
    this.handlers.add(handler);
    return () => {
      this.handlers.delete(handler);
    };
  }

  disconnect(): void {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
    this.handlers.clear();
  }
}
