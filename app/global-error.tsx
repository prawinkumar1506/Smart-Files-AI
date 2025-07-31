'use client'
import { useState, useEffect } from "react"
export default function GlobalError() {
    useEffect(() => {
        const originalWarn = console.warn;
        console.warn = (...args) => {
            if (!args[0].includes('preload')) {
                originalWarn.apply(console, args);
            }
        };
        return () => { console.warn = originalWarn; };
    }, []);

    return (
        <html>
        <body>
        {/* Error content */}
        </body>
        </html>
    )
}
