// OneDrive from the page: sign-in by hand-written PKCE (no library), list a shared folder, and a
// file's short-lived download URL. Ported from frontends/browser-tests/onedrive.js.

import { m } from "../paraglide/messages.js";
import { opens, takes } from "./chosen";

const CLIENT_ID = "45bf3d02-6c45-4b46-b66c-3a7e562f9c1c"; // same Entra app as the Python player
const AUTHORITY = "https://login.microsoftonline.com/consumers";
const SCOPES = "Files.ReadWrite offline_access"; // personal accounts need it to open a share link
const GRAPH = "https://graph.microsoft.com/v1.0";
const MEDIA = [".mp3", ".wav", ".pdf"];
const TOKENS = "downtempo-onedrive";
const PENDING = "downtempo-onedrive-pending";

export type RemoteFile = { path: string; size: number; modified: string; drive: string; id: string };
export type Tokens = { access: string; refresh: string; expires: number; signedIn: number };

// Must equal a redirect URI in Entra exactly, so "index.html" is dropped.
export const redirectUri = () => location.origin + location.pathname.replace(/index\.html$/, "");

export const base64url = (bytes: ArrayBuffer | Uint8Array) =>
  btoa(String.fromCharCode(...new Uint8Array(bytes)))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");

const randomText = () => base64url(crypto.getRandomValues(new Uint8Array(32)));

/** Leaves the page for Microsoft's sign-in; it comes back to `redirectUri()` with a code. */
export async function signIn() {
  const verifier = randomText();
  const state = randomText();
  sessionStorage.setItem(PENDING, JSON.stringify({ verifier, state }));
  const challenge = base64url(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier)));
  const query = new URLSearchParams({
    client_id: CLIENT_ID,
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
  localStorage.removeItem(TOKENS);
}

export function signedIn(): Tokens | null {
  try {
    const tokens = JSON.parse(localStorage.getItem(TOKENS) || "null") as Tokens | null;
    return tokens?.refresh ? tokens : null;
  } catch {
    return null;
  }
}

/** After the redirect back: trade the code for tokens. Returns false when the page wasn't a redirect. */
export async function finishSignIn(): Promise<boolean> {
  const params = new URLSearchParams(location.search);
  if (!params.has("code") && !params.has("error")) return false;
  history.replaceState(null, "", redirectUri());
  if (params.has("error")) {
    throw new Error(m.signin_refused({ reason: params.get("error_description") || params.get("error") || "" }));
  }
  const pending = JSON.parse(sessionStorage.getItem(PENDING) || "{}");
  sessionStorage.removeItem(PENDING);
  if (params.get("state") !== pending.state) throw new Error(m.signin_mismatch());
  await tokenRequest({
    grant_type: "authorization_code",
    code: params.get("code") ?? "",
    redirect_uri: redirectUri(),
    code_verifier: pending.verifier,
  });
  return true;
}

async function tokenRequest(fields: Record<string, string>): Promise<Tokens> {
  const response = await fetch(`${AUTHORITY}/oauth2/v2.0/token`, {
    method: "POST",
    body: new URLSearchParams({ client_id: CLIENT_ID, scope: SCOPES, ...fields }),
  });
  const body = await response.json();
  if (!response.ok) {
    if (body.error === "invalid_grant") signOut(); // the sign-in ran out (SPA refresh tokens last 24 h)
    throw new SignInNeeded(m.signin_again_code({ code: body.error }));
  }
  const tokens: Tokens = {
    access: body.access_token,
    refresh: body.refresh_token,
    expires: Date.now() + (body.expires_in - 60) * 1000,
    signedIn: signedIn()?.signedIn || Date.now(),
  };
  localStorage.setItem(TOKENS, JSON.stringify(tokens));
  return tokens;
}

export class SignInNeeded extends Error {}

let refreshing: Promise<Tokens> | null = null;

async function accessToken(): Promise<string> {
  const tokens = signedIn();
  if (!tokens) throw new SignInNeeded(m.signin_first());
  if (Date.now() < tokens.expires) return tokens.access;
  refreshing ??= tokenRequest({ grant_type: "refresh_token", refresh_token: tokens.refresh }).finally(
    () => (refreshing = null),
  );
  return (await refreshing).access;
}

async function graph(url: string, headers: Record<string, string> = {}) {
  const response = await fetch(url.startsWith("http") ? url : GRAPH + url, {
    headers: { Authorization: `Bearer ${await accessToken()}`, ...headers },
  });
  const body = await response.json();
  if (response.status === 401) throw new SignInNeeded(m.signin_asks());
  if (!response.ok)
    throw new Error(m.onedrive_answered({ status: response.status, reason: body.error?.message ?? body.error?.code }));
  return body;
}

/** A sharing URL as a Graph share id (u!<unpadded base64url>), as the Python provider does. */
export function shareId(link: string): string {
  let url = link.trim();
  const redeem = new URL(url).searchParams.get("redeem");
  if (redeem) url = atob(redeem.replace(/-/g, "+").replace(/_/g, "/"));
  return "u!" + base64url(new TextEncoder().encode(url));
}

export function looksLikeLink(text: string): boolean {
  try {
    const host = new URL(text.trim()).hostname;
    return /(^|\.)(1drv\.ms|onedrive\.live\.com|sharepoint\.com|onedrive\.com)$/.test(host);
  } catch {
    return false;
  }
}

async function children(drive: string, item: string) {
  const items = [];
  let next: string | undefined = `/drives/${drive}/items/${item}/children`;
  while (next) {
    const page = await graph(next);
    items.push(...page.value);
    next = page["@odata.nextLink"];
  }
  return items;
}

export type Share = { name: string; drive: string; id: string };
export type Folder = { id: string; name: string; path: string; items: number; size: number }; // size: all inside

/** The shared folder behind the link. */
export async function openShare(link: string): Promise<Share> {
  const root = await graph(`/shares/${shareId(link)}/driveItem`, { Prefer: "redeemSharingLink" });
  if (!root.folder) throw new Error(m.link_is_file());
  return { name: root.name, drive: root.parentReference.driveId, id: root.id };
}

/** The folders right inside one folder of the share (`below`: its path, "" for the top). */
export async function subfolders(share: Share, item: string, below: string): Promise<Folder[]> {
  return (await children(share.drive, item))
    .filter((child) => child.folder)
    .map((child) => ({
      id: child.id,
      name: child.name,
      path: below ? `${below}/${child.name}` : child.name,
      items: child.folder.childCount ?? 0,
      size: child.size ?? 0,
    }))
    .sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }));
}

/** Every media file in the chosen folders of the share (all of it when none are chosen), any depth,
 * except in the left-out ones. Only folders on the way to a chosen one are opened, never a left-out
 * one. `onFolder` hears each folder as it is read. */
export async function listShare(
  link: string,
  folders: string[] = [],
  skip: string[] = [],
  onFolder: (path: string) => void = () => {},
) {
  const root = await openShare(link);
  const found: RemoteFile[] = [];
  async function walk(item: string, below: string) {
    onFolder(below || root.name);
    for (const child of await children(root.drive, item)) {
      const path = below ? `${below}/${child.name}` : child.name;
      if (child.folder) {
        if (opens(folders, path, skip)) await walk(child.id, path);
      } else if (takes(folders, path, skip) && MEDIA.some((end) => child.name.toLowerCase().endsWith(end))) {
        found.push({ path, size: child.size, modified: child.lastModifiedDateTime, drive: root.drive, id: child.id });
      }
    }
  }
  await walk(root.id, "");
  return { name: root.name, files: found };
}

/** The file's pre-signed download URL (not /content: its redirect breaks CORS). */
export async function downloadUrl(file: RemoteFile): Promise<string> {
  const item = await graph(`/drives/${file.drive}/items/${file.id}?select=id,@microsoft.graph.downloadUrl`);
  return item["@microsoft.graph.downloadUrl"];
}
