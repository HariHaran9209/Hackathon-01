/**
 * Pitchly WebSocket Manager
 * Maintains live two-way connection for board and suggestion updates.
 */

export function createProjectSocket(projectId, onMessage, onStatusChange) {
  let ws = null;
  let reconnectTimeout = null;
  let isClosedManually = false;
  let attempts = 0;

  function getSocketUrl() {
    if (import.meta.env.VITE_WS_URL) {
      let wsUrl = import.meta.env.VITE_WS_URL.trim();
      if (!/^wss?:\/\//i.test(wsUrl)) {
        wsUrl = wsUrl.startsWith('localhost') || wsUrl.startsWith('127.0.0.1')
          ? `ws://${wsUrl}`
          : `wss://${wsUrl}`;
      }
      return `${wsUrl.replace(/\/+$/, '')}/ws/projects/${projectId}/`;
    }

    if (import.meta.env.VITE_API_URL) {
      let apiUrl = import.meta.env.VITE_API_URL.trim();
      if (!/^https?:\/\//i.test(apiUrl)) {
        apiUrl = apiUrl.startsWith('localhost') || apiUrl.startsWith('127.0.0.1')
          ? `http://${apiUrl}`
          : `https://${apiUrl}`;
      }
      const wsUrl = apiUrl.replace(/^http:\/\//i, 'ws://').replace(/^https:\/\//i, 'wss://');
      return `${wsUrl.replace(/\/+$/, '')}/ws/projects/${projectId}/`;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/ws/projects/${projectId}/`;
  }

  function connect() {
    if (isClosedManually) return;

    try {
      const url = getSocketUrl();
      ws = new WebSocket(url);

      ws.onopen = () => {
        attempts = 0;
        if (onStatusChange) onStatusChange('connected');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (onMessage) onMessage(data);
        } catch (e) {
          console.warn('[WS] Failed to parse message JSON:', event.data);
        }
      };

      ws.onclose = (event) => {
        if (onStatusChange) onStatusChange('disconnected');
        if (!isClosedManually) {
          const delay = Math.min(1000 * Math.pow(1.5, attempts), 8000);
          attempts++;
          reconnectTimeout = setTimeout(connect, delay);
        }
      };

      ws.onerror = (error) => {
        console.warn('[WS] Socket error:', error);
        ws.close();
      };
    } catch (err) {
      console.warn('[WS] Connection exception:', err);
      const delay = Math.min(1000 * Math.pow(1.5, attempts), 8000);
      attempts++;
      reconnectTimeout = setTimeout(connect, delay);
    }
  }

  connect();

  return {
    send(data) {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(data));
      }
    },
    close() {
      isClosedManually = true;
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (ws) ws.close();
    },
  };
}
