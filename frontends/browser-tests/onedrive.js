// OneDrive from a web page: sign-in by hand-written PKCE (no library), then Graph calls.
import { AUTHORITY, ONEDRIVE_CLIENT_ID, SCOPES } from "./settings.js";

const GRAPH = "https://graph.microsoft.com/v1.0";
const MEDIA = [".mp3", ".wav", ".pdf"];
const TOKENS = "downtempo-test-tokens";
const PENDING = "downtempo-test-pending";

// Must equal a redirect URI in Entra exactly, so "index.html" is dropped.
export const redirectUri = () => location.origin + location.pathname.replace(/index\.html$/, "");

const base64url = (bytes) =>
  btoa(String.fromCharCode(...new Uint8Array(bytes)))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");

const randomText = () => base64url(crypto.getRandomValues(new Uint8Array(32)));

export async function signIn() {
  const verifier = randomText();
  const state = randomText();
  sessionStorage.setItem(PENDING, JSON.stringify({ verifier, state }));
  const challenge = base64url(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier)));
  const query = new URLSearchParams({
    client_id: ONEDRIVE_CLIENT_ID,
    response_type: "code",
    redirect_uri: redirectUri(),
    response_mode: "query",
    scope: SCOPES,
    state,
    code_challenge: challenge,
    code_challenge_method: "S256",
  });
  location.assign(`${AUTHORITY}/oauth2/v2.0/authorize?${query}`);
}

export function signOut() {
  sessionStorage.removeItem(TOKENS);
}

/** After the redirect back: trade the code for tokens. Returns false when the page wasn't a redirect. */
export async function finishSignIn() {
  const params = new URLSearchParams(location.search);
  if (!params.has("code") && !params.has("error")) return false;
  history.replaceState(null, "", redirectUri());
  if (params.has("error")) {
    throw new Error(`Sign-in refused: ${params.get("error")}: ${params.get("error_description")}`);
  }
  const pending = JSON.parse(sessionStorage.getItem(PENDING) || "{}");
  sessionStorage.removeItem(PENDING);
  if (params.get("state") !== pending.state) throw new Error("Sign-in answer doesn't match this tab (state); try again.");
  await tokenRequest({
    grant_type: "authorization_code",
    code: params.get("code"),
    redirect_uri: redirectUri(),
    code_verifier: pending.verifier,
  });
  return true;
}

async function tokenRequest(fields) {
  const response = await fetch(`${AUTHORITY}/oauth2/v2.0/token`, {
    method: "POST",
    body: new URLSearchParams({ client_id: ONEDRIVE_CLIENT_ID, scope: SCOPES, ...fields }),
  });
  const body = await response.json();
  if (!response.ok) throw new Error(`Token request failed: ${body.error}: ${body.error_description}`);
  const tokens = {
    access: body.access_token,
    refresh: body.refresh_token,
    expires: Date.now() + (body.expires_in - 60) * 1000,
    signedIn: JSON.parse(sessionStorage.getItem(TOKENS) || "{}").signedIn || Date.now(),
  };
  sessionStorage.setItem(TOKENS, JSON.stringify(tokens));
  return tokens;
}

export function signedIn() {
  return JSON.parse(sessionStorage.getItem(TOKENS) || "null");
}

async function accessToken() {
  const tokens = signedIn();
  if (!tokens) throw new Error("Not signed in.");
  if (Date.now() < tokens.expires) return tokens.access;
  return (await tokenRequest({ grant_type: "refresh_token", refresh_token: tokens.refresh })).access;
}

async function graph(url, headers = {}) {
  const response = await fetch(url.startsWith("http") ? url : GRAPH + url, {
    headers: { Authorization: `Bearer ${await accessToken()}`, ...headers },
  });
  const body = await response.json();
  if (!response.ok) throw new Error(`Graph ${response.status}: ${body.error?.code}: ${body.error?.message}`);
  return body;
}

/** A sharing URL as a Graph share id (u!<unpadded base64url>), as the Python provider does. */
function shareId(link) {
  let url = link.trim();
  const redeem = new URL(url).searchParams.get("redeem");
  if (redeem) url = atob(redeem.replace(/-/g, "+").replace(/_/g, "/"));
  return "u!" + base64url(new TextEncoder().encode(url));
}

async function children(drive, item) {
  const items = [];
  let next = `/drives/${drive}/items/${item}/children`;
  while (next) {
    const page = await graph(next);
    items.push(...page.value);
    next = page["@odata.nextLink"];
  }
  return items;
}

/** Every media file under the shared folder: { path, size, drive, id }. */
export async function listShare(link, onFolder) {
  const root = await graph(`/shares/${shareId(link)}/driveItem`, { Prefer: "redeemSharingLink" });
  if (!root.folder) throw new Error("The link opens a file, not a folder.");
  const drive = root.parentReference.driveId;
  const found = [];
  async function walk(item, below) {
    onFolder(below || root.name);
    for (const child of await children(drive, item)) {
      const path = below ? `${below}/${child.name}` : child.name;
      if (child.folder) await walk(child.id, path);
      else if (MEDIA.some((end) => child.name.toLowerCase().endsWith(end))) {
        found.push({ path, size: child.size, drive, id: child.id });
      }
    }
  }
  await walk(root.id, "");
  return { name: root.name, files: found };
}

/** The file's short-lived, pre-signed download URL (not /content: its redirect breaks CORS). */
export async function downloadUrl(file) {
  const item = await graph(`/drives/${file.drive}/items/${file.id}?select=id,@microsoft.graph.downloadUrl`);
  return item["@microsoft.graph.downloadUrl"];
}
