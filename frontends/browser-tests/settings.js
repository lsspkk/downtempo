// The test pages' settings. Nothing here is secret: a client id only names the app at sign-in.
// Same Entra registration as the Python app (src/downtempo/downloaders/onedrive.py); it needs a
// "Single-page application" platform with this page's address as redirect URI.
export const ONEDRIVE_CLIENT_ID = "45bf3d02-6c45-4b46-b66c-3a7e562f9c1c";
export const AUTHORITY = "https://login.microsoftonline.com/consumers";
// Personal accounts need Files.ReadWrite to open a share link (Graph's shares docs).
export const SCOPES = "Files.ReadWrite offline_access";
