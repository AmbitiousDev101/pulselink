"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { getUrlResult, type URLResponse } from "@/lib/api";

export default function UrlResultPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [data, setData] = useState<URLResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;

    const fetchResult = async () => {
      try {
        const result = await getUrlResult(id);
        setData(result);
        setLoading(false);

        if (result.status === "processing") {
          interval = setInterval(async () => {
            try {
              const updated = await getUrlResult(id);
              setData(updated);
              if (updated.status !== "processing") {
                clearInterval(interval);
              }
            } catch {
              clearInterval(interval);
            }
          }, 2000);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load result");
        setLoading(false);
      }
    };

    fetchResult();
    return () => clearInterval(interval);
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-[#94a3b8]">Loading analysis...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="glass-card p-8 text-center max-w-md">
          <p className="text-red-400 mb-4">{error}</p>
          <button
            onClick={() => router.push("/")}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-white transition-colors"
          >
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const result = data.result;
  const isProcessing = data.status === "processing";

  const safetyConfig: Record<string, { bg: string; text: string; border: string }> = {
    safe: { bg: "bg-emerald-500/20", text: "text-emerald-400", border: "border-emerald-500/30" },
    suspicious: { bg: "bg-amber-500/20", text: "text-amber-400", border: "border-amber-500/30" },
    dangerous: { bg: "bg-red-500/20", text: "text-red-400", border: "border-red-500/30" },
  };

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="border-b border-[#2d2d44]/50">
        <div className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
          <a href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
            </div>
            <span className="text-xl font-bold text-white tracking-tight">PulseLink</span>
          </a>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-6 py-10">
        {/* Back button */}
        <button
          onClick={() => router.push("/")}
          className="flex items-center gap-2 text-[#94a3b8] hover:text-white mb-6 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back
        </button>

        {/* Processing State */}
        {isProcessing && (
          <div className="glass-card p-10 text-center mb-8 animate-pulse-glow">
            <div className="w-16 h-16 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin mx-auto mb-6" />
            <h2 className="text-2xl font-bold text-white mb-2">Analyzing URL...</h2>
            <p className="text-[#94a3b8]">{data.url}</p>
            <p className="text-sm text-[#4a5568] mt-4">This usually takes 5-15 seconds</p>
          </div>
        )}

        {/* Completed Result */}
        {result && !isProcessing && (
          <div className="space-y-6 animate-fade-in-up">
            {/* Title Card */}
            <div className="glass-card p-8">
              <div className="flex items-start justify-between gap-4 mb-4">
                <div className="flex-1">
                  <h1 className="text-3xl font-bold text-white mb-2">
                    {result.title || "No title"}
                  </h1>
                  <a href={data.url} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:text-indigo-300 transition-colors break-all">
                    {data.url}
                  </a>
                  {result.description && (
                    <p className="text-[#94a3b8] mt-3">{result.description}</p>
                  )}
                </div>
                {result.safety_score && (
                  <div className={`px-5 py-2 rounded-xl text-lg font-bold border ${safetyConfig[result.safety_score]?.bg} ${safetyConfig[result.safety_score]?.text} ${safetyConfig[result.safety_score]?.border}`}>
                    {result.safety_score.charAt(0).toUpperCase() + result.safety_score.slice(1)}
                  </div>
                )}
              </div>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="glass-card p-5 text-center">
                <div className="text-sm text-[#94a3b8] mb-1">Status Code</div>
                <div className="text-2xl font-bold text-white">
                  {result.status_code || "—"}
                </div>
              </div>
              <div className="glass-card p-5 text-center">
                <div className="text-sm text-[#94a3b8] mb-1">Response Time</div>
                <div className="text-2xl font-bold text-white">
                  {result.response_time_ms ? `${Math.round(result.response_time_ms)}ms` : "—"}
                </div>
              </div>
              <div className="glass-card p-5 text-center">
                <div className="text-sm text-[#94a3b8] mb-1">SSL</div>
                <div className={`text-2xl font-bold ${result.ssl_valid ? "text-emerald-400" : "text-red-400"}`}>
                  {result.ssl_valid ? "Valid" : "Invalid"}
                </div>
              </div>
              <div className="glass-card p-5 text-center">
                <div className="text-sm text-[#94a3b8] mb-1">Redirects</div>
                <div className="text-2xl font-bold text-white">
                  {result.redirect_chain.length}
                </div>
              </div>
            </div>

            {/* SSL Details */}
            {result.ssl_expires_at && (
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold text-white mb-3">SSL Certificate</h3>
                <div className="flex items-center gap-4 text-sm">
                  <span className="text-[#94a3b8]">Expires:</span>
                  <span className="text-white">{result.ssl_expires_at}</span>
                </div>
              </div>
            )}

            {/* Redirect Chain */}
            {result.redirect_chain.length > 0 && (
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold text-white mb-3">Redirect Chain</h3>
                <div className="space-y-2">
                  {result.redirect_chain.map((url, i) => (
                    <div key={i} className="flex items-center gap-3 text-sm">
                      <span className="w-6 h-6 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center text-xs font-bold shrink-0">
                        {i + 1}
                      </span>
                      <span className="text-[#94a3b8] truncate">{url}</span>
                    </div>
                  ))}
                  <div className="flex items-center gap-3 text-sm">
                    <span className="w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-xs font-bold shrink-0">
                      ✓
                    </span>
                    <span className="text-emerald-400 truncate">{data.url}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Tech Stack */}
            {result.tech_stack.length > 0 && (
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold text-white mb-3">Tech Stack Detected</h3>
                <div className="flex flex-wrap gap-2">
                  {result.tech_stack.map((tech, i) => (
                    <span key={i} className="px-4 py-2 bg-indigo-500/15 text-indigo-300 rounded-xl border border-indigo-500/20 text-sm font-medium">
                      {tech}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Screenshot */}
            {result.screenshot_url && (
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold text-white mb-3">Screenshot</h3>
                <div className="rounded-xl overflow-hidden border border-[#2d2d44]">
                  <img
                    src={result.screenshot_url}
                    alt={`Screenshot of ${data.url}`}
                    className="w-full"
                  />
                </div>
              </div>
            )}

            {/* Metadata */}
            <div className="text-center text-xs text-[#4a5568] pt-4">
              Analyzed at {result.analyzed_at ? new Date(result.analyzed_at).toLocaleString() : "—"}
              {" · "}
              Job ID: {data.id}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
