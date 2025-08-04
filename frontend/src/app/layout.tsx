import { AuthKitProvider } from '@workos-inc/authkit-nextjs/components';

import type { Metadata } from 'next';

import './globals.css';

export const metadata: Metadata = {
  title: 'ProfeshGPT',
  description: 'Lorem Ipsum',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body suppressHydrationWarning>
        <AuthKitProvider>{children}</AuthKitProvider>
      </body>
    </html>
  );
}
