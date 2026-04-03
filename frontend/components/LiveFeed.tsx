"use client";

import { useState, useEffect, useCallback } from "react";
import wsManager, { WS_URL } from "@/lib/websocket";

interface FeedItem {
  id: string;
  url: string;
  title?: string;
  safety_score?: string;
  response_time_ms?: number;
  analyzed_at?: string;
}

export default function LiveFeed() {
  const [items, setItems] = useState<FeedItem[]>([]);
  const [connected, setConnected] = useState(false);

  const handleMessage = useCallback((data: unknown) => {
    const item = data as FeedItem;
    setItems((prev) => [item, ...prev].slice(0, 20));
  }, []);

  useEffect(() => {
    console.log(`Attempting WebSocket connection to: ${WS_URL}/ws/feed`);
    wsManager.connect();
    const unsub = wsManager.onMessage(handleMessage);

    const checkConnection = setInterval(() => {
      setConnected(wsManager.isConnected);
    }, 1000);

    return () => {
      unsub();
      clearInterval(checkConnection);
      wsManager.disconnect();
    };
  }, []);

  const safetyColor = (score?: string) => {
    switch (score) {
      case "safe":
        return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
      case "suspicious":
        return "bg-amber-500/20 text-amber-400 border-amber-500/30";
      case "dangerous":
        return "bg-red-500/20 text-red-400 border-red-500/30";
      default:
        return "bg-gray-500/20 text-gray-400 border-gray-500/30";
    }
  };

  const formatTime = (ts?: string) => {
    if (!ts) return "";
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    } catch {
      return "";
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto mt-12">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-semibold text-white">Live Feed</h2>
          <div className="flex items-center gap-2">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                connected ? "bg-emerald-400 animate-pulse" : "bg-red-400"
              }`}
            />
            <span className="text-xs text-[#94a3b8] font-medium">
              {connected ? "Live" : "Connecting..."}
            </span>
          </div>
        </div>
        <span className="text-xs text-[#4a5568]">
          {items.length} recent {items.length === 1 ? "analysis" : "analyses"}
        </span>
      </div>

      {/* Feed Items */}
      <div className="space-y-2">
        {items.length === 0 ? (
          <div className="glass-card p-8 text-center">
            <div className="text-[#4a5568] text-lg mb-2">No analyses yet</div>
            <p className="text-[#4a5568] text-sm">
              Submit a URL above or click &quot;Simulate Live Traffic&quot; to see the feed in action
            </p>
          </div>
        ) : (
          items.map((item, index) => (
            <div
              key={`${item.id}-${index}`}
              className="glass-card p-4 animate-slide-in"
              style={{ animationDelay: `${index * 30}ms` }}
            >
              <div className="flex items-center justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <a
                    href={`/urls/${item.id}`}
                    className="text-sm text-white font-medium hover:text-indigo-400 transition-colors truncate block"
                  >
                    {item.url.length > 60
                      ? item.url.substring(0, 60) + "..."
                      : item.url}
                  </a>
                  {item.title && (
                    <p className="text-xs text-[#94a3b8] truncate mt-0.5">
                      {item.title}
                    </p>
                  )}
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  {item.safety_score && (
                    <span
                      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${safetyColor(
                        item.safety_score
                      )}`}
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-current" />
                      {item.safety_score.charAt(0).toUpperCase() +
                        item.safety_score.slice(1)}
                    </span>
                  )}

                  {item.response_time_ms && (
                    <span className="text-xs text-[#94a3b8] font-mono">
                      {Math.round(item.response_time_ms)}ms
                    </span>
                  )}

                  <span className="text-xs text-[#4a5568]">
                    {formatTime(item.analyzed_at)}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
