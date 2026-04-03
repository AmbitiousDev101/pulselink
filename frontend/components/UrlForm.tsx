"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { submitUrl, URLResponse } from "@/lib/api";
import ResultCard from "@/components/ResultCard";

export default function UrlForm() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cachedResult, setCachedResult] = useState<URLResponse | null>(null);
  const router = useRouter();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setError(null);
    setCachedResult(null);

    try {
      const result = await submitUrl(url.trim());

      // If we got the full cached result back
      if ("result" in result) {
        setCachedResult(result as URLResponse);
      } else {
        // Queued for processing
        router.push(`/urls/${result.job_id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative group">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-500 rounded-2xl opacity-30 group-hover:opacity-60 blur transition-all duration-500" />
          <div className="relative flex items-center bg-[#1a1a2e] rounded-2xl border border-[#2d2d44] overflow-hidden">
            <div className="pl-5 text-[#94a3b8]">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                />
              </svg>
            </div>
            <input
              id="url-input"
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Paste any URL to analyze..."
              className="flex-1 bg-transparent px-4 py-5 text-white text-lg placeholder-[#4a5568] focus:outline-none"
              disabled={loading}
            />
            <button
              id="analyze-button"
              type="submit"
              disabled={loading || !url.trim()}
              className="m-2 px-8 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold rounded-xl transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg
                    className="animate-spin h-4 w-4"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  Analyzing...
                </span>
              ) : (
                "Analyze"
              )}
            </button>
          </div>
        </div>
      </form>

      {error && (
        <div className="mt-4 p-4 bg-red-900/30 border border-red-500/30 rounded-xl text-red-400 text-sm animate-fade-in-up">
          {error}
        </div>
      )}

      {cachedResult && (
        <div className="mt-8 animate-fade-in-up text-left">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-emerald-400 font-medium">Instant Result (Cached)</span>
          </div>
          <ResultCard id={cachedResult.id} url={cachedResult.url} result={cachedResult.result} />
        </div>
      )}
    </div>
  );
}
