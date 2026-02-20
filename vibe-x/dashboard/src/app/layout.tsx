import type { Metadata } from 'next';
import './globals.css';
import { AppShell } from './AppShell';

export const metadata: Metadata = {
  title: 'VIBE-X Dashboard',
  description: 'Team Intelligence Dashboard — VIBE-X',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" className="dark">
      <body className="antialiased">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
