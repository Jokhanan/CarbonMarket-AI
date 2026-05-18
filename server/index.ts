import express, { type Request, Response, NextFunction } from "express";
import * as http from "http";
import { registerRoutes } from "./routes";
import { serveStatic } from "./static";
import { createServer } from "http";

const app = express();
const httpServer = createServer(app);

declare module "http" {
  interface IncomingMessage {
    rawBody: unknown;
  }
}

// ── FastAPI reverse proxy ──────────────────────────────────────────────────
// MUST be placed before express.json() so raw request bodies (including
// multipart file uploads) are piped unmodified. Express strips the "/api"
// prefix before the handler runs, so req.url already equals the FastAPI path.
app.use("/api", (req: Request, res: Response) => {
  const targetPath = req.url || "/";

  const proxyReq = http.request(
    {
      hostname: "localhost",
      port: 3000,
      path: targetPath,
      method: req.method,
      headers: { ...req.headers, host: "localhost:3000" },
    },
    (proxyRes) => {
      res.writeHead(proxyRes.statusCode ?? 200, proxyRes.headers);
      proxyRes.pipe(res, { end: true });
    }
  );

  proxyReq.on("error", (err) => {
    console.error("[proxy] FastAPI error:", err.message);
    if (!res.headersSent) {
      res.writeHead(502, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: "FastAPI backend unavailable", detail: err.message }));
    }
  });

  req.pipe(proxyReq, { end: true });
});

// ── Body parsers (non-API routes only) ────────────────────────────────────
app.use(
  express.json({
    verify: (req, _res, buf) => {
      req.rawBody = buf;
    },
  })
);
app.use(express.urlencoded({ extended: false }));

// ── Request logger ────────────────────────────────────────────────────────
export function log(message: string, source = "express") {
  const formattedTime = new Date().toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
  });
  console.log(`${formattedTime} [${source}] ${message}`);
}

// ── Start ─────────────────────────────────────────────────────────────────
(async () => {
  await registerRoutes(httpServer, app);

  app.use((err: any, _req: Request, res: Response, next: NextFunction) => {
    const status = err.status || err.statusCode || 500;
    const message = err.message || "Internal Server Error";
    console.error("Internal Server Error:", err);
    if (res.headersSent) return next(err);
    return res.status(status).json({ message });
  });

  if (process.env.NODE_ENV === "production") {
    serveStatic(app);
  } else {
    const { setupVite } = await import("./vite");
    await setupVite(httpServer, app);
  }

  const port = parseInt(process.env.PORT || "5000", 10);
  httpServer.listen({ port, host: "0.0.0.0", reusePort: true }, () => {
    log(`serving on port ${port}`);
  });
})();
