import type { Metadata } from 'next'
import './globals.css'
import { Inter } from 'next/font/google'
const inter = Inter({ subsets: ['latin'] })
export const metadata: Metadata = {
    title: 'Smart Files AI',
    description: 'Created by Prawin Kumar S',
    generator: 'prawin',
}

export default function RootLayout({
                                       children,
                                   }: Readonly<{
    children: React.ReactNode
}>) {
    return (
        <html lang="en" suppressHydrationWarning>
        <body className={inter.className} suppressHydrationWarning>
        {children}
        </body>
        </html>
    )
}
