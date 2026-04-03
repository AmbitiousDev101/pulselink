"use client";

import Link from "next/link";
import type { URLResult } from "@/lib/api";

interface ResultCardProps {
  id: string;
  url: string;
  result: URLResult | null;
  compact?: boolean;
}

function SafetyBadge({ score }: { score: string | null }) {
  const config = {
    safe: { bg: "bg-emerald-500/20", text: "text-emerald-400", border: "border-emerald-500/30", label: "Safe" },
    suspicious: { bg: "bg-amber-500/20", text: "text-amber-400", border: "border-amber-500/30", label: "Suspicious" },
    dangerous: { bg: "bg-red-500/20", text: "text-red-400", border: "border-red-500/30", label: "Dangerous" },
  };

  const c = config[score as keyof typeof config] || config.safe;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${c.bg} ${c.text} border ${c.border}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {c.label}
    </span>
  );
}

export default function ResultCard({ id, url, result, compact = false }: ResultCardProps) {
  if (!result) return null;

  if (compact) {
    return (
      <Link href={`/urls/${id}`}>
        <div className="glass-card p-4 cursor-pointer animate-fade-in-up hover:border-indigo-500/40 transition-all duration-300">
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1 min-w-0">
              <p className="text-sm text-white font-medium truncate">{url}</p>
              {result.title && (
                <p className="text-xs text-[#94a3b8] truncate mt-0.5">{result.title}</p>
              )}
            </div>
            <div className="flex items-center gap-3 shrink-0">
              <SafetyBadge score={result.safety_score} />
              {result.response_time_ms && (
                <span className="text-xs text-[#94a3b8] font-mono">
                  {Math.round(result.response_time_ms)}ms
                </span>
              )}
            </div>
          </div>
        </div>
      </Link>
    );
  }

  return (
    <Link href={`/urls/${id}`}>
      <div className="glass-card p-6 cursor-pointer hover:border-indigo-500/40 transition-all duration-300">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-white truncate">
              {result.title || url}
            </h3>
            <p className="text-sm text-indigo-400 truncate mt-1">{url}</p>
            {result.description && (
              <p className="text-sm text-[#94a3b8] mt-2 line-clamp-2">{result.description}</p>
            )}
          </div>
          <SafetyBadge score={result.safety_score} />
        </div>

        <div className="flex flex-wrap items-center gap-4 text-sm">
          {/* Response Time */}
          {result.response_time_ms && (
            <div className="flex items-center gap-1.5 text-[#94a3b8]">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="font-mono">{Math.round(result.response_time_ms)}ms</span>
            </div>
          )}

          {/* SSL Status */}
          <div className="flex items-center gap-1.5">
            {result.ssl_valid ? (
              <span className="text-emerald-400 flex items-center gap-1">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                SSL Valid
              </span>
            ) : (
              <span className="text-red-400 flex items-center gap-1">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z" />
                </svg>
                SSL Invalid
              </span>
            )}
          </div>

          {/* Redirect Count */}
          {result.redirect_chain.length > 0 && (
            <div className="flex items-center gap-1.5 text-[#94a3b8]">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
              {result.redirect_chain.length} redirect{result.redirect_chain.length > 1 ? "s" : ""}
            </div>
          )}
        </div>

        {/* Tech Stack Pills */}
        {result.tech_stack.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-4">
            {result.tech_stack.map((tech, i) => (
              <span
                key={i}
                className="px-2.5 py-1 text-xs font-medium bg-indigo-500/15 text-indigo-300 rounded-lg border border-indigo-500/20"
              >
                {tech}
              </span>
            ))}
          </div>
        )}

        {/* Screenshot Thumbnail */}
        {result.screenshot_url && (
          <div className="mt-4 rounded-lg overflow-hidden border border-[#2d2d44]">
            <img
              src={result.screenshot_url}
              alt={`Screenshot of ${url}`}
              className="w-full h-40 object-cover object-top"
            />
          </div>
        )}
      </div>
    </Link>
  );
}
