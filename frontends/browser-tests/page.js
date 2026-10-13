// The test page: wires sign-in, folder listing, download + play and storage to the HTML.
import * as onedrive from "./onedrive.js";
import * as storage from "./storage.js";

const $ = (id) => document.getElementById(id);
const LINK = "downtempo-test-link";

function log(text, bad = false) {
  const line = `${new Date().toLocaleTimeString()} ${text}\n`;
  $("log").textContent += line;
  if (bad) console.error(text);
}

const megabytes = (bytes) => `${(bytes / 1e6).toFixed(1)} MB`;
const savedName = (path) => path.replaceAll("/", " › ");

function button(text, onClick) {
  const element = document.createElement("button");
  element.textContent = text;
  element.onclick = onClick;
  return element;
}

function row(table, ...cells) {
  const tr = table.insertRow();
  for (const cell of cells) {
    const td = tr.insertCell();
    if (cell instanceof Node) td.append(cell);
    else td.textContent = cell;
  }
  return tr;
}

// 1. Sign-in

function showSignIn() {
  const tokens = onedrive.signedIn();
  $("sign-status").textContent = tokens
    ? `Signed in at ${new Date(tokens.signedIn).toLocaleTimeString()} (this tab only).`
    : `Not signed in. Redirect address: ${onedrive.redirectUri()}`;
  $("sign-in").hidden = !!tokens;
  $("sign-out").hidden = !tokens;
}

$("sign-in").onclick = () => onedrive.signIn();
$("sign-out").onclick = () => {
  onedrive.signOut();
  log("Signed out.");
  showSignIn();
};

// 2. Listing and downloading

async function listFiles() {
  const link = $("link").value.trim();
  if (!link) return;
  try { localStorage.setItem(LINK, link); } catch {}
  $("files").replaceChildren();
  const started = performance.now();
  try {
    const share = await onedrive.listShare(link, (folder) => ($("list-status").textContent = `Listing ${folder}…`));
    const seconds = ((performance.now() - started) / 1000).toFixed(1);
    const total = share.files.reduce((sum, f) => sum + f.size, 0);
    $("list-status").textContent = `${share.name}: ${share.files.length} media files, ${megabytes(total)} (${seconds} s).`;
    log(`Listed "${share.name}": ${share.files.length} files, ${megabytes(total)} in ${seconds} s.`);
    for (const file of share.files) {
      const status = document.createElement("span");
      status.className = "muted";
      row($("files"), file.path, megabytes(file.size), button("Download & play", () => download(file, status)), status)
        .cells[1].className = "n";
    }
  } catch (error) {
    $("list-status").textContent = error.message;
    $("list-status").className = "bad";
    log(`Listing failed: ${error.message}`, true);
  }
}

async function download(file, status) {
  const started = performance.now();
  try {
    status.textContent = "asking…";
    const url = await onedrive.downloadUrl(file);
    const response = await fetch(url);
    if (!response.ok) throw new Error(`download answered ${response.status}`);
    await storage.save(savedName(file.path), response, (bytes) => {
      status.textContent = `${Math.round((100 * bytes) / file.size)} %`;
    });
    const seconds = ((performance.now() - started) / 1000).toFixed(1);
    status.textContent = `saved (${seconds} s)`;
    log(`Downloaded ${file.path}, ${megabytes(file.size)} in ${seconds} s.`);
    await showSaved();
    play(savedName(file.path));
  } catch (error) {
    status.textContent = error.message;
    status.className = "bad";
    log(`Download of ${file.path} failed: ${error.message}`, true);
  }
}

$("list").onclick = listFiles;
$("link").onkeydown = (event) => event.key === "Enter" && listFiles();

// 3. Storage

async function showSaved() {
  const { usage, quota, kept } = await storage.usage();
  $("storage-status").textContent =
    `Used ${megabytes(usage)} of ${megabytes(quota)} allowed. ` +
    (kept ? "Kept: the browser won't clear these files by itself." : "May be cleared by the browser when the disk fills.");
  $("keep").hidden = kept;
  $("saved").replaceChildren();
  const saved = await storage.list();
  if (!saved.length) row($("saved"), "No files on this device yet: press Download & play on a file above.");
  for (const file of saved) {
    row(
      $("saved"),
      file.name,
      megabytes(file.size),
      button(file.name.toLowerCase().endsWith(".pdf") ? "Open" : "Play", () => play(file.name)),
      button("Delete", async () => {
        await storage.remove(file.name);
        log(`Deleted ${file.name}.`);
        await showSaved();
      }),
    ).cells[1].className = "n";
  }
}

async function play(name) {
  try {
    const url = URL.createObjectURL(await storage.open(name));
    if (name.toLowerCase().endsWith(".pdf")) window.open(url);
    else {
      $("player").src = url;
      // Browsers refuse to start sound a while after the click (a long download); the player
      // then shows the file and ▶ starts it.
      await $("player").play().catch(() => log("Loaded in the player below: press ▶ to start."));
    }
    log(`Opened ${name} from the device.`);
  } catch (error) {
    log(`Opening ${name} failed: ${error.message}`, true);
  }
}

$("keep").onclick = async () => {
  const kept = await storage.askToKeep();
  log(`Asked to keep files: ${kept ? "yes" : "no (the browser decides from how the site is used)"}.`);
  await showSaved();
};

$("copy-log").onclick = () => navigator.clipboard.writeText(`${navigator.userAgent}\n${$("log").textContent}`);

// Start

async function start() {
  log(`Page opened: ${navigator.userAgent}`);
  try { $("link").value = localStorage.getItem(LINK) || ""; } catch {}
  try {
    if (await onedrive.finishSignIn()) log("Signed in.");
  } catch (error) {
    log(error.message, true);
  }
  showSignIn();
  try {
    await showSaved();
  } catch (error) {
    $("storage-status").textContent = `Private file system not available: ${error.message}`;
    log(`Storage failed: ${error.message}`, true);
  }
}

start();
