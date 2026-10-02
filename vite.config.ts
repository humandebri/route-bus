import { defineConfig } from 'vite'
import { cloudflare } from '@cloudflare/vite-plugin'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import react from '@vitejs/plugin-react'
export default defineConfig({ server: { watch: { ignored: ['**/test-results/**','**/build/**','**/data/raw/**','**/.wrangler/**'] } }, plugins: [cloudflare({ persistState: { path: '.wrangler/organized-preview' }, viteEnvironment: { name: 'ssr' } }), tanstackStart(), react()] })
