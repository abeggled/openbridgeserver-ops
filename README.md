# openbridgeserver-ops

Kanal-Manifest-Repo für [openbridgeserver](https://github.com/abeggled/openbridgeserver).
Implementiert Phase 2 von [#655](https://github.com/abeggled/openbridgeserver/issues/655)
([#945](https://github.com/abeggled/openbridgeserver/issues/945)) — kanalbasierte
Update-Fähigkeit (`canary → staging → stable`) für Docker- und LXC-Artefakte.

## Kanäle

| Kanal | Zweck |
|---|---|
| `canary` | Bleeding edge — wird automatisch nach jedem erfolgreichen Release-Tag-Push im Hauptrepo befüllt (inkl. Release Candidates). |
| `staging` | Manuell aus `canary` promotet, zum Testen vor der Freigabe an Endnutzer. |
| `stable` | Manuell aus `staging` promotet — das ist der Kanal, den Standard-Installationen verwenden sollten. |

Jeder Kanal hat eine Manifest-Datei unter `channels/<kanal>.json`:

```json
{
  "channel": "stable",
  "version": "2026.7.0",
  "docker": {
    "image": "ghcr.io/abeggled/openbridgeserver",
    "digest": "sha256:..."
  },
  "lxc": {
    "version": "2026.7.0",
    "asset_url": "https://github.com/abeggled/openbridgeserver/releases/download/2026.7.0/openbridgeserver-app-bundle_2026.7.0.tar.gz",
    "sha256": "..."
  },
  "promoted_at": "2026-07-15T10:00:00Z",
  "promoted_by": "starwarsfan"
}
```

Solange ein Kanal noch keine Version hat, sind `version`, `docker`, `lxc`, `promoted_at` und
`promoted_by` `null`. `obs-update --channel=<name>` bricht in diesem Fall mit einer klaren
Fehlermeldung ab, statt eine leere/fehlerhafte Installation zu versuchen.

`docker` wird von Docker-Compose-Deployments konsumiert (Pull per Digest:
`docker pull <image>@<digest>`), `lxc` von `obs-update` auf LXC-Installationen. Beide Blöcke
werden unabhängig voneinander befüllt/promotet.

## Automatischer Canary-Write

Nach jedem erfolgreichen Tag-Push im Hauptrepo schreiben `release.yml` (Docker-Digest) und
`lxc-template.yml` (LXC-Bundle-URL + SHA-256) automatisch in `channels/canary.json`. Das
erfordert im Hauptrepo einen Repo-Secret `OPS_REPO_TOKEN` mit Schreibzugriff auf dieses Repo
(siehe Setup unten).

## Promotion & Rollback

Manuell über den Workflow **Actions → Promote channel → Run workflow** in diesem Repo
(`.github/workflows/promote.yml`):

- **Promote**: `action=promote`, `channel=staging` (übernimmt `canary`) oder `channel=stable`
  (übernimmt `staging`).
- **Rollback**: `action=rollback`, `channel=<staging|stable>`, optional `ref` (Git-SHA/Tag des
  gewünschten vorherigen Stands von `channels/<channel>.json`). Leer gelassen wird automatisch
  der vorherige Commit verwendet, der diese Datei geändert hat.

Der Workflow committet das Ergebnis direkt auf `main` (Standard-`GITHUB_TOKEN`, kein
zusätzliches Secret nötig, da alles same-repo passiert).

## Setup-Checkliste (einmalig, manuell)

1. Im Hauptrepo (`abeggled/openbridgeserver`) ein fine-grained Personal Access Token
   `OPS_REPO_TOKEN` anlegen: Repository access → nur dieses Repo
   (`abeggled/openbridgeserver-ops`), Permissions → `Contents: Read and write`.
2. Das Token als Repository-Secret `OPS_REPO_TOKEN` im Hauptrepo hinterlegen
   (Settings → Secrets and variables → Actions).
3. Optional: Branch Protection auf `main` in diesem Repo aktivieren, Required Status Check =
   der `test`-Job aus `.github/workflows/test.yml`.
