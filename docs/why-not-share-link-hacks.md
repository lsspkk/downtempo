# Rejected approaches: anonymous share link, cookies, the "Badger" token

**Summary**: Decided. Anonymous OneDrive share calls return 401 since late 2024; copying cookies or the "Badger" token was rejected as fragile and unsupported. Use Entra + MSAL + Graph ([onedrive.md](onedrive.md)).

The first version of the downloader called
`https://api.onedrive.com/v1.0/shares/u!.../driveItem` anonymously, with an optional copied
browser `Cookie`. It now fails with **HTTP 401 Unauthorized**.

## What happened

- Since late 2024, the anonymous personal-OneDrive shares API fails. Old share ids return
  `400 bad argument`, and encoded URLs return
  `401 UnauthenticatedVroomException`. Microsoft has not updated its documentation.
  Sources: [msqa-2138092-shares-api-behavior](web/msqa-2138092-shares-api-behavior.txt),
  [github-onedrive-api-docs-1555](web/github-onedrive-api-docs-1555.txt),
  [msqa-2130053-direct-link-conversion](web/msqa-2130053-direct-link-conversion.txt)
- Microsoft also discontinued "public" folders in personal OneDrive.
  Source: [dajbych-public-folders-discontinued](web/dajbych-public-folders-discontinued.txt)
- Microsoft says anonymous Graph access without a signed-in user is not supported.
  Sources: [msqa-1195727-anonymous-graph](web/msqa-1195727-anonymous-graph.txt),
  [msqa-5011486-anonymous-js](web/msqa-5011486-anonymous-js.txt)

## The workaround people reverse-engineered (don't use it)

The OneDrive web app gets a "Badger" token from `POST https://api-badgerp.svc.ms/v1.0/token`
with the web app's own `appId`. It then calls
`https://my.microsoftpersonalcontent.com/_api/v2.0/shares/...` with `Authorization: Badger <token>`.
Source: [codez-one-badger-api](web/codez-one-badger-api.txt)

It is undocumented and impersonates Microsoft's own client, it has no SLA, and it can break at
any time. Copying browser cookies into `.env` has the same problems, and it also leaks a session.

## Conclusion

Use Entra app registration + MSAL + Microsoft Graph. See [onedrive.md](onedrive.md).
