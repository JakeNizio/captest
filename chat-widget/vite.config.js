import { defineConfig } from "vite";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  build: {
    lib: {
      entry: fileURLToPath(new URL("./src/widget.js", import.meta.url)),
      name: "AiChatWidget",
      fileName: () => "widget.js",
      formats: ["iife"],
    },
  },
  server: {
    host: "0.0.0.0",
    port: 4000,
  },
});
