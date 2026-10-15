import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: 'Winterfell · Westeros Explorer', description: 'An original, explorable northern fortress. Walk through its gates, discover the courtyard, and inspect the craft behind the world.' };
export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }
