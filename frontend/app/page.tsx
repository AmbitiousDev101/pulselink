import UrlForm from "@/components/UrlForm";
import LiveFeed from "@/components/LiveFeed";
import SimulateButton from "@/components/SimulateButton";

export default function Home() {
  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="border-b border-[#2d2d44]/50">
        <div className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <svg
                className="w-5 h-5 text-white"
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
            <span className="text-xl font-bold text-white tracking-tight">
              PulseLink
            </span>
          </div>
          <nav className="flex items-center gap-4">
            <a
              href="/docs"
              className="text-sm text-[#94a3b8] hover:text-white transition-colors"
            >
              API Docs
            </a>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-b from-indigo-500/5 via-transparent to-transparent pointer-events-none" />
        <div className="absolute top-20 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-indigo-500/10 rounded-full blur-[120px] pointer-events-none" />

        <div className="relative max-w-6xl mx-auto px-6 pt-20 pb-12 text-center">
          <h1 className="text-5xl md:text-6xl font-extrabold text-white mb-4 tracking-tight">
            Real-Time URL{" "}
            <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              Intelligence
            </span>
          </h1>
          <p className="text-lg text-[#94a3b8] max-w-xl mx-auto mb-12">
            Paste any URL. Get instant analysis — title, response time, SSL status,
            redirect chain, tech stack, and safety score.
          </p>

          <UrlForm />

          {/* Stats bar */}
          <div className="flex items-center justify-center gap-8 mt-10 text-sm text-[#4a5568]">
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Under 50ms API response
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              SSL &amp; Security checks
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              Live screenshot capture
            </div>
          </div>
          
          <div className="mt-8 flex justify-center fade-in-up" style={{ animationDelay: "200ms" }}>
            <SimulateButton />
          </div>
        </div>
      </section>

      {/* Live Feed */}
      <section className="max-w-6xl mx-auto px-6 pb-20">
        <LiveFeed />
      </section>
    </main>
  );
}
