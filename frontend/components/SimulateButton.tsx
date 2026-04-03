"use client";

import { useState } from "react";
import { simulateTraffic } from "@/lib/api";

export default function SimulateButton() {
  const [loading, setLoading] = useState(false);

  const handleSimulate = async () => {
    setLoading(true);
    try {
      await simulateTraffic();
    } catch (error) {
      console.error(error);
    } finally {
      // Simulate button loading state stays for an extra half second for UX
      setTimeout(() => setLoading(false), 500);
    }
  };

  return (
    <button
      onClick={handleSimulate}
      disabled={loading}
      className="px-4 py-2 bg-gradient-to-r from-[#2d2d44] to-[#1e1e2e] hover:from-[#3d3d5c] hover:to-[#2d2d44] text-white rounded-xl transition-all shadow-sm font-medium border border-[#4a4a6a] disabled:opacity-50 flex items-center gap-2 text-sm"
    >
      {loading ? (
        <>
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
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
          Simulating...
        </>
      ) : (
        <>
          <svg
            className="w-4 h-4 text-indigo-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
          Simulate Live Traffic
        </>
      )}
    </button>
  );
}
