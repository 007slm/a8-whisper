import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from "path"

// https://vitejs.dev/config/
export default defineConfig({
    base: './', // Essential for loading in PySide6 WebEngine via file://
    plugins: [react()],
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./src"),
        },
    },
    server: {
        host: true, // expose to network/tauri
        port: 5173,
        strictPort: true, // fail if port is in use, don't fallback to 5174
    },
})
