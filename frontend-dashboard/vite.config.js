import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 3000,
    // Docker Desktop bind mounts on Windows often miss inotify events.
    watch: {
      usePolling: true,
      interval: 300,
    },
  },
});
