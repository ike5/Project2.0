import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Slack Clone",
  description: "A production-ready Slack clone built in the course.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
