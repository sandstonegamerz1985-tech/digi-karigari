import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import './globals.css';
export const metadata: Metadata = { title: 'Digi Karigari | Handmade, rooted in heritage', description: 'A digital marketplace connecting Indian artisans directly with buyers.' };
export default function RootLayout({children}:{children:ReactNode}) { return <html lang="en"><body>{children}</body></html>; }
