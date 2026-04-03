import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PulseLink — Real-Time URL Intelligence",
  description:
    "Analyze any URL instantly. Get page details, SSL status, tech stack, safety score, and live screenshots. Watch the global feed in real time.",
  keywords: ["URL analysis", "security", "tech stack detection", "SSL checker"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased min-h-screen">{children}</body>
    </html>
  );
}
