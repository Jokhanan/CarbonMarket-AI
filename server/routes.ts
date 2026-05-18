import type { Express } from "express";
import { type Server } from "http";

export async function registerRoutes(
  httpServer: Server,
  _app: Express
): Promise<Server> {
  // All /api/* routes are handled by the FastAPI proxy in server/index.ts
  return httpServer;
}
