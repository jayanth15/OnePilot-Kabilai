// Production server for the TanStack Start (Vite) build.
// Serves static assets from dist/client and forwards other requests to the
// SSR web handler (Request -> Response) exported by dist/server/server.js.

import { createServer } from "node:http"
import { extname, join, resolve, normalize } from "node:path"
import { readFile } from "node:fs/promises"
import { fileURLToPath } from "node:url"
import { Readable } from "node:stream"

const __dirname = fileURLToPath(new URL(".", import.meta.url))
const port = Number(process.env.APP_PORT || process.env.PORT || 3000)
const clientDir = resolve(__dirname, "dist/client")

// Lazy-load the built SSR handler (produced by `npm run build`).
const serverModule = await import("./dist/server/server.js")
const buildFetch = serverModule.server_default?.fetch || serverModule.default?.fetch

if (typeof buildFetch !== "function") {
  console.error("dist/server/server.js did not export a fetch handler. Run `npm run build` first.")
  process.exit(1)
}

const MIME = {
  ".html": "text/html",
  ".js": "text/javascript",
  ".mjs": "text/javascript",
  ".css": "text/css",
  ".json": "application/json",
  ".png": "image/png",
  ".ico": "image/x-icon",
  ".svg": "image/svg+xml",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
  ".webmanifest": "application/manifest+json",
  ".txt": "text/plain",
}

// Convert Node http.IncomingMessage -> Web Request.
async function toWebRequest(req) {
  const url = `http://${req.headers.host || `localhost:${port}`}${req.url || "/"}`
  const headers = new Headers()
  for (const [k, v] of Object.entries(req.headers)) {
    if (v !== undefined) headers.set(k, Array.isArray(v) ? v.join(", ") : v)
  }
  const body = req.method === "GET" || req.method === "HEAD" ? undefined : Readable.toWeb(req)
  return new Request(url, { method: req.method, headers, body, duplex: "half" })
}

async function sendWebResponse(res, webRes) {
  res.writeHead(webRes.status, Object.fromEntries(webRes.headers.entries()))
  if (webRes.body) {
    for await (const chunk of webRes.body) res.write(chunk)
  }
  res.end()
}

const server = createServer(async (req, res) => {
  try {
    const pathname = (req.url || "/").split("?")[0]
    const safePath = normalize(pathname).replace(/^(\.\.(\/|\\|$))+/, "")
    const filePath = join(clientDir, safePath === "/" ? "index.html" : safePath)

    // Serve static client assets if present; otherwise pass to SSR handler.
    if (filePath.startsWith(clientDir) && pathname !== "/") {
      try {
        const data = await readFile(filePath)
        res.writeHead(200, {
          "Content-Type": MIME[extname(filePath)] || "application/octet-stream",
          "Cache-Control": "no-cache",
        })
        res.end(data)
        return
      } catch {
        // not a static file — fall through to SSR
      }
    }

    const webRes = await buildFetch(await toWebRequest(req))
    sendWebResponse(res, webRes)
  } catch (err) {
    console.error("Request failed:", err)
    if (!res.headersSent) {
      res.writeHead(500)
      res.end("Internal Server Error")
    } else {
      res.end()
    }
  }
})

server.listen(port, () => {
  console.log(`Kabilai frontend server listening on http://0.0.0.0:${port}`)
})
