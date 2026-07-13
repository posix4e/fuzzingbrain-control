import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const siteUrl = "https://posix4e.github.io/fuzzingbrain-control";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: "FuzzingBrain Control",
  description:
    "A pinned, reproducible model baseline for FuzzingBrain and future fuzzer integrations.",
  openGraph: {
    title: "FuzzingBrain Control",
    description: "A fixed point for fuzzer progress.",
    url: siteUrl,
    images: [
      {
        url: `${siteUrl}/og.png`,
        width: 1536,
        height: 1024,
      },
    ],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "FuzzingBrain Control",
    description: "A fixed point for fuzzer progress.",
    images: [`${siteUrl}/og.png`],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        {children}
      </body>
    </html>
  );
}
