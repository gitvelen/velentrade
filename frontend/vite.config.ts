import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiProxyTarget = process.env.VELENTRADE_API_PROXY_TARGET ?? "http://127.0.0.1:8000";

export default defineConfig({
  root: "frontend",
  plugins: [react()],
  server: {
    port: 8443,
    proxy: {
      "/api": {
        target: apiProxyTarget,
        changeOrigin: true,
      },
    },
  },
});
