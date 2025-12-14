import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
  preview: {
    // Railway uses a public hostname like *.up.railway.app. Vite preview blocks
    // unknown hosts by default, so we allow Railway + local dev hosts.
    allowedHosts: ["localhost", "127.0.0.1", ".up.railway.app"],
  },
});


