import assert from "node:assert/strict";
import { spawn, spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdtemp, readFile, readdir, rm } from "node:fs/promises";
import { createServer, request as httpRequest } from "node:http";
import { tmpdir } from "node:os";
import { dirname, extname, join, resolve, sep } from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import { fileURLToPath } from "node:url";

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const siteRoot = resolve(projectRoot, "site");
const publicBase = "/conversation-success-coach/";

if (typeof WebSocket !== "function") {
  throw new Error("The public-site browser test requires Node.js 22 or newer.");
}
if (!existsSync(join(siteRoot, "index.html"))) {
  throw new Error(`Static site not found at ${siteRoot}.`);
}

async function collectTextFiles(directory) {
  const files = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...await collectTextFiles(path));
    } else if ([".css", ".drawio", ".html", ".js", ".json", ".svg"].includes(extname(entry.name))) {
      files.push(path);
    }
  }
  return files;
}

for (const file of await collectTextFiles(siteRoot)) {
  const contents = await readFile(file, "utf8");
  assert.doesNotMatch(
    contents,
    /https?:\/\/[^"'\s]*execute-api|wss:\/\/|\.amazonaws\.com/i,
    `Public artifact contains a private cloud endpoint marker: ${file}`,
  );
}

const contentTypes = {
  ".css": "text/css; charset=utf-8",
  ".drawio": "application/xml; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
};

function findChrome() {
  const candidates = [
    process.env.CHROME_BIN,
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
  ].filter(Boolean);
  for (const candidate of candidates) {
    if (existsSync(candidate)) return candidate;
  }
  for (const command of ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]) {
    const found = spawnSync("which", [command], { encoding: "utf8" });
    if (found.status === 0 && found.stdout.trim()) return found.stdout.trim();
  }
  throw new Error("Chrome or Chromium is required for the public-site browser test.");
}

async function startStaticServer() {
  const server = createServer(async (request, response) => {
    try {
      const url = new URL(request.url || "/", "http://127.0.0.1");
      let pathname = decodeURIComponent(url.pathname);
      if (pathname === publicBase.slice(0, -1) || pathname === publicBase) {
        pathname = `${publicBase}index.html`;
      }
      if (!pathname.startsWith(publicBase)) {
        response.writeHead(404).end("Not found");
        return;
      }
      const relativePath = pathname.slice(publicBase.length);
      const filePath = resolve(siteRoot, relativePath);
      if (filePath !== siteRoot && !filePath.startsWith(`${siteRoot}${sep}`)) {
        response.writeHead(403).end("Forbidden");
        return;
      }
      const body = await readFile(filePath);
      response.writeHead(200, {
        "cache-control": "no-store",
        "content-type": contentTypes[extname(filePath)] || "application/octet-stream",
      });
      if (request.method === "HEAD") response.end();
      else response.end(body);
    } catch {
      response.writeHead(404).end("Not found");
    }
  });
  await new Promise((resolveListen, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolveListen);
  });
  const address = server.address();
  const port = typeof address === "object" && address ? address.port : 0;
  return { server, origin: `http://127.0.0.1:${port}` };
}

function requestJson(url, method = "GET") {
  return new Promise((resolveRequest, reject) => {
    const request = httpRequest(url, { method }, (response) => {
      let body = "";
      response.setEncoding("utf8");
      response.on("data", (chunk) => {
        body += chunk;
      });
      response.on("end", () => {
        if (!response.statusCode || response.statusCode < 200 || response.statusCode >= 300) {
          reject(new Error(`HTTP ${response.statusCode || "unknown"}: ${body}`));
          return;
        }
        try {
          resolveRequest(JSON.parse(body));
        } catch (error) {
          reject(new Error(`Invalid JSON from ${url}: ${error}`));
        }
      });
    });
    request.setTimeout(2_000, () => request.destroy(new Error(`Timed out requesting ${url}`)));
    request.once("error", reject);
    request.end();
  });
}

async function waitForDevToolsUrl(chrome, getOutput) {
  for (let attempt = 0; attempt < 120; attempt += 1) {
    if (chrome.exitCode !== null) {
      throw new Error(`Chrome exited before DevTools became available (code ${chrome.exitCode}).`);
    }
    const match = getOutput().match(/DevTools listening on (ws:\/\/\S+)/);
    if (match) return match[1];
    await delay(100);
  }
  throw new Error("Timed out waiting for Chrome to announce its DevTools endpoint.");
}

class CdpSession {
  constructor(socket) {
    this.socket = socket;
    this.nextId = 1;
    this.pending = new Map();
    this.listeners = new Map();
    socket.addEventListener("message", (event) => {
      const message = JSON.parse(String(event.data));
      if (message.id) {
        const pending = this.pending.get(message.id);
        if (!pending) return;
        this.pending.delete(message.id);
        if (message.error) pending.reject(new Error(message.error.message));
        else pending.resolve(message.result || {});
        return;
      }
      for (const listener of this.listeners.get(message.method) || []) {
        listener(message.params || {});
      }
    });
  }

  static async connect(url) {
    const socket = new WebSocket(url);
    await new Promise((resolveOpen, reject) => {
      socket.addEventListener("open", resolveOpen, { once: true });
      socket.addEventListener("error", reject, { once: true });
    });
    return new CdpSession(socket);
  }

  send(method, params = {}) {
    const id = this.nextId;
    this.nextId += 1;
    return new Promise((resolveResult, reject) => {
      this.pending.set(id, { resolve: resolveResult, reject });
      this.socket.send(JSON.stringify({ id, method, params }));
    });
  }

  on(method, listener) {
    const listeners = this.listeners.get(method) || new Set();
    listeners.add(listener);
    this.listeners.set(method, listeners);
  }

  once(method, timeoutMs = 10_000) {
    return new Promise((resolveEvent, reject) => {
      const listener = (params) => {
        clearTimeout(timer);
        this.listeners.get(method)?.delete(listener);
        resolveEvent(params);
      };
      const timer = setTimeout(() => {
        this.listeners.get(method)?.delete(listener);
        reject(new Error(`Timed out waiting for Chrome event ${method}`));
      }, timeoutMs);
      const listeners = this.listeners.get(method) || new Set();
      listeners.add(listener);
      this.listeners.set(method, listeners);
    });
  }

  close() {
    this.socket.close();
  }
}

async function evaluate(cdp, expression) {
  const result = await cdp.send("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
  });
  if (result.exceptionDetails) {
    throw new Error(
      result.exceptionDetails.exception?.description
      || result.exceptionDetails.text
      || "Browser evaluation failed",
    );
  }
  return result.result?.value;
}

async function waitFor(cdp, expression, description, timeoutMs = 10_000) {
  const deadline = Date.now() + timeoutMs;
  let lastError;
  while (Date.now() < deadline) {
    try {
      const value = await evaluate(cdp, expression);
      if (value) return value;
    } catch (error) {
      lastError = error;
    }
    await delay(60);
  }
  throw new Error(`Timed out waiting for ${description}${lastError ? `: ${lastError}` : ""}`);
}

async function click(cdp, selector) {
  const clicked = await evaluate(cdp, `(() => {
    const element = document.querySelector(${JSON.stringify(selector)});
    if (!element || element.disabled) return false;
    element.scrollIntoView({ block: "center", inline: "center" });
    element.click();
    return true;
  })()`);
  assert.equal(clicked, true, `Missing or disabled clickable element ${selector}`);
  await delay(80);
}

async function navigate(cdp, url) {
  const loaded = cdp.once("Page.loadEventFired");
  await cdp.send("Page.navigate", { url });
  await loaded;
}

function waitForProcessExit(process, timeoutMs) {
  if (process.exitCode !== null || process.signalCode !== null) return Promise.resolve(true);
  return new Promise((resolveExit) => {
    const onExit = () => {
      clearTimeout(timer);
      resolveExit(true);
    };
    const timer = setTimeout(() => {
      process.off("exit", onExit);
      resolveExit(false);
    }, timeoutMs);
    process.once("exit", onExit);
  });
}

const { server, origin } = await startStaticServer();
const profileDir = await mkdtemp(join(tmpdir(), "conversation-coach-pages-chrome-"));
const chromePath = findChrome();
let chromeOutput = "";
const chromeArgs = [
  "--headless",
  "--disable-background-networking",
  "--disable-component-update",
  "--disable-default-apps",
  "--disable-dev-shm-usage",
  "--disable-extensions",
  "--disable-gpu",
  "--disable-sync",
  "--metrics-recording-only",
  "--mute-audio",
  "--no-default-browser-check",
  "--no-first-run",
  "--remote-debugging-address=127.0.0.1",
  "--remote-debugging-port=0",
  `--user-data-dir=${profileDir}`,
  "--window-size=1440,1000",
  "about:blank",
];
if (process.platform === "linux") chromeArgs.unshift("--no-sandbox");

const chrome = spawn(chromePath, chromeArgs, { stdio: ["ignore", "pipe", "pipe"] });
for (const stream of [chrome.stdout, chrome.stderr]) {
  stream.setEncoding("utf8");
  stream.on("data", (chunk) => {
    chromeOutput = `${chromeOutput}${chunk}`.slice(-12_000);
  });
}

let cdp;
const browserExceptions = [];
const consoleErrors = [];
const requestedUrls = [];
const webSocketUrls = [];
const networkFailures = [];
const badResponses = [];

try {
  const browserWebSocketUrl = await waitForDevToolsUrl(chrome, () => chromeOutput);
  const devToolsOrigin = `http://${new URL(browserWebSocketUrl).host}`;
  const target = await requestJson(
    `${devToolsOrigin}/json/new?${encodeURIComponent("about:blank")}`,
    "PUT",
  );
  cdp = await CdpSession.connect(target.webSocketDebuggerUrl);
  await cdp.send("Page.enable");
  await cdp.send("Runtime.enable");
  await cdp.send("Network.enable");

  cdp.on("Runtime.exceptionThrown", ({ exceptionDetails }) => {
    browserExceptions.push(
      exceptionDetails?.exception?.description || exceptionDetails?.text || "Unknown exception",
    );
  });
  cdp.on("Runtime.consoleAPICalled", ({ type, args }) => {
    if (type === "error") {
      consoleErrors.push(args.map((arg) => arg.value || arg.description || "").join(" "));
    }
  });
  cdp.on("Network.requestWillBeSent", ({ request }) => {
    if (request?.url) requestedUrls.push(request.url);
  });
  cdp.on("Network.webSocketCreated", ({ url }) => {
    if (url) webSocketUrls.push(url);
  });
  cdp.on("Network.loadingFailed", ({ errorText, type, blockedReason }) => {
    networkFailures.push({ errorText, type, blockedReason });
  });
  cdp.on("Network.responseReceived", ({ response }) => {
    if (response?.status >= 400) badResponses.push({ status: response.status, url: response.url });
  });

  await navigate(cdp, `${origin}${publicBase}?public-site=true`);
  await waitFor(
    cdp,
    `document.documentElement.dataset.publicSite === "true"
      && document.querySelector("h1")?.innerText.includes("Better conversations")
      && !document.querySelector("[data-public-preview]").hidden`,
    "the canonical landing page",
  );
  const landing = await evaluate(cdp, `(() => ({
    copy: document.body.innerText,
    dashboardHref: document.querySelector('a[href="dashboard.html"]')?.href,
    architectureHref: document.querySelector('a[href="architecture.html"]')?.href,
    apiHref: document.querySelector("[data-local-api-link]")?.href,
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
  }))()`);
  assert.match(landing.copy, /Published synthetic preview/i);
  assert.match(landing.copy, /Fictional demo data only/i);
  assert.equal(landing.dashboardHref, `${origin}${publicBase}dashboard.html`);
  assert.equal(landing.architectureHref, `${origin}${publicBase}architecture.html`);
  assert.equal(
    landing.apiHref,
    "https://github.com/hk-775/conversation-success-coach/blob/main/docs/API.md",
  );
  assert.ok(landing.overflow <= 1, `Landing page overflows by ${landing.overflow}px`);

  await navigate(cdp, `${origin}${publicBase}architecture.html?public-site=true`);
  await waitFor(
    cdp,
    `document.documentElement.dataset.publicSite === "true"
      && document.querySelectorAll(".architecture-diagram-card img").length === 2
      && [...document.querySelectorAll(".architecture-diagram-card img")]
        .every((image) => image.complete && image.naturalWidth >= 1000)`,
    "the architecture explorer and rendered diagrams",
  );
  await click(cdp, '[data-flow-scenario="privacy"]');
  await waitFor(
    cdp,
    `document.querySelector("[data-flow-title]")?.innerText.includes("privacy lifecycle")`,
    "the privacy architecture scenario",
  );
  await click(cdp, "[data-flow-play]");
  await waitFor(
    cdp,
    `document.querySelector("[data-flow-play]")?.getAttribute("aria-label") === "Pause journey"`,
    "the running architecture animation",
  );
  await click(cdp, "[data-flow-play]");
  const pausedStatus = await evaluate(cdp, `document.querySelector("[data-flow-status]").innerText`);
  await delay(1_700);
  assert.equal(
    await evaluate(cdp, `document.querySelector("[data-flow-status]").innerText`),
    pausedStatus,
  );
  const diagramLinks = await evaluate(cdp, `[...document.querySelectorAll(".architecture-diagram-card a[download]")].map((link) => link.href)`);
  assert.equal(diagramLinks.length, 4);
  diagramLinks.forEach((href) => assert.ok(href.startsWith(`${origin}${publicBase}assets/`)));

  await navigate(cdp, `${origin}${publicBase}dashboard.html?public-site=true`);
  await waitFor(
    cdp,
    `document.documentElement.dataset.publicSite === "true"
      && document.querySelector("[data-api-status]")?.innerText.includes("Published synthetic preview")
      && document.querySelector("[data-scenario-select]")?.options.length === 4`,
    "the published dashboard dataset",
  );
  const publishedControls = await evaluate(cdp, `(() => ({
    reset: document.querySelector("[data-reset-demo]")?.disabled,
    savePrivacy: document.querySelector("[data-save-privacy]")?.disabled,
    purge: document.querySelector("[data-purge-conversation]")?.disabled,
    newPlaybook: document.querySelector("[data-open-playbook]")?.disabled,
    turnText: document.querySelector("[data-turn-form] textarea")?.disabled,
  }))()`);
  assert.deepEqual(publishedControls, {
    reset: true,
    savePrivacy: true,
    purge: true,
    newPlaybook: true,
    turnText: true,
  });

  await click(cdp, '[data-view-target="workspace"]');
  await evaluate(cdp, `(() => {
    const select = document.querySelector("[data-scenario-select]");
    select.value = "conv_community_cedar";
    select.dispatchEvent(new Event("change", { bubbles: true }));
  })()`);
  await waitFor(
    cdp,
    `document.querySelector("[data-conversation-title]")?.innerText.includes("Cedar Commons")`,
    "the community scenario",
  );
  await click(cdp, "[data-analyze]");
  await waitFor(
    cdp,
    `document.querySelector("[data-analyze]")?.disabled === false
      && Number(document.querySelector("[data-suggestion-count]")?.innerText) === 3`,
    "the browser-local synthetic analysis",
  );

  for (const view of ["suggestions", "feedback", "playbooks", "privacy", "audit", "guided"]) {
    await click(cdp, `[data-view-target="${view}"]`);
    assert.equal(
      await evaluate(cdp, `document.querySelector('[data-view="${view}"]').classList.contains("active")`),
      true,
      `${view} view did not activate`,
    );
  }
  await click(cdp, "[data-start-tour]");
  await waitFor(cdp, `document.querySelector("[data-tour-dialog]")?.open === true`, "the guided tour");
  await click(cdp, "[data-tour-close]");

  await cdp.send("Emulation.setDeviceMetricsOverride", {
    deviceScaleFactor: 1,
    height: 844,
    mobile: true,
    width: 390,
  });
  await navigate(cdp, `${origin}${publicBase}dashboard.html?public-site=true`);
  await waitFor(
    cdp,
    `document.querySelector("[data-api-status]")?.innerText.includes("Published synthetic preview")`,
    "the mobile dashboard",
  );
  const mobileOverflow = await evaluate(
    cdp,
    `document.documentElement.scrollWidth - document.documentElement.clientWidth`,
  );
  assert.ok(mobileOverflow <= 1, `Mobile dashboard overflows by ${mobileOverflow}px`);

  const apiRequests = requestedUrls.filter((rawUrl) => {
    const url = new URL(rawUrl);
    return url.origin === origin && url.pathname.startsWith("/api/");
  });
  const externalRequests = requestedUrls.filter((rawUrl) => {
    const url = new URL(rawUrl);
    return ["http:", "https:"].includes(url.protocol)
      && (url.origin !== origin || !url.pathname.startsWith(publicBase));
  });
  assert.deepEqual(apiRequests, [], `Published site called an API: ${apiRequests.join(", ")}`);
  assert.deepEqual(externalRequests, [], `Published site made external requests: ${externalRequests.join(", ")}`);
  assert.deepEqual(webSocketUrls, [], `Published site opened WebSockets: ${webSocketUrls.join(", ")}`);
  assert.deepEqual(networkFailures, [], `Network failures: ${JSON.stringify(networkFailures)}`);
  assert.deepEqual(badResponses, [], `Bad responses: ${JSON.stringify(badResponses)}`);
  assert.deepEqual(browserExceptions, [], `Browser exceptions: ${browserExceptions.join("\n")}`);
  assert.deepEqual(consoleErrors, [], `Console errors: ${consoleErrors.join("\n")}`);

  console.log("Public landing, dashboard, architecture, diagrams, mobile layout, and no-network boundary passed.");
} finally {
  cdp?.close();
  server.close();
  if (chrome.exitCode === null) chrome.kill("SIGTERM");
  if (!(await waitForProcessExit(chrome, 2_000)) && chrome.exitCode === null) {
    chrome.kill("SIGKILL");
    await waitForProcessExit(chrome, 2_000);
  }
  await rm(profileDir, {
    force: true,
    maxRetries: 10,
    recursive: true,
    retryDelay: 100,
  });
}
