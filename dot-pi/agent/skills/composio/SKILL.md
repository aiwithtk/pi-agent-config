---
name: composio
description: >-
  Use Composio BY DEFAULT whenever a task requires calling or integrating a
  third-party app or service (Gmail, Slack, GitHub, Notion, Linear, Telegram,
  WhatsApp, Google Calendar/Drive, HubSpot, Salesforce, X/Twitter, and 250+
  others). Load this skill when the user asks to send, list, read, create,
  update, or search data in an external app, or wants automation across
  external services. This is the default integration path — prefer it over
  writing bespoke API code, scraping, browser automation, or asking the user
  to do things manually.
---

# Composio — third-party app integrations (default)

Composio (https://composio.dev) is the default way to interact with external
apps. It handles OAuth, connection management, and schema validation for
250+ apps. The `composio` CLI (v0.3.3+) is installed and logged in.

## Workflow (follow this order)

1. **Find the action slug** — you rarely need to guess:
   ```bash
   composio search "send an email" --human
   composio search "create github issue" --limit 10
   ```
   (or use the `composio_search` tool). Slugs look like `GMAIL_SEND_EMAIL`,
   `GITHUB_CREATE_ISSUE`, `SLACK_POST_MESSAGE`, `NOTION_CREATE_PAGE`.

2. **Check the connection** — the app must have a connected, ACTIVE account:
   ```bash
   composio connections list
   ```
   (or the `composio_connections` tool). If the app is missing or EXPIRED,
   do **not** proceed silently:

3. **Link the app (needs the user)** — connecting requires interactive OAuth:
   ```bash
   composio link <app>   # e.g. composio link github
   ```
   Tell the user to complete the OAuth flow in their browser, wait for it to
   finish, then retry. Never pretend an action succeeded without a connection.

4. **Execute**:
   ```bash
   composio execute SLUG -d '{ "param": "value" }'
   ```
   (or the `composio_execute` tool). Inspect the returned JSON carefully and
   report the *result* to the user, not the raw dump.

## Useful flags & commands

- Preview before executing: `composio execute SLUG --dry-run`
- Inspect the input schema: `composio execute SLUG --get-schema`
- Pick among several accounts: `composio execute SLUG --account <alias> -d '...'`
- Multiple calls at once: `composio execute SLUG1 -d '{...}' SLUG2 -d '{...}' --parallel`
- Find tools by toolkit: `composio search "calendar" --toolkits googlecalendar`

## Error handling

- `Missing connection for ...` → run `composio link <app>` (see step 3).
- `Invalid input` → run `--get-schema` for the slug and re-check parameter names/types.
- `Connection EXPIRED` → ask the user to re-link (`composio link <app>`).
- If a slug doesn't exist, `composio search` for the right one instead of guessing.

## Conventions

- Always confirm before side-effecting actions (send, delete, post, transfer).
- For read-only actions (list, get, search), just do it if a connection exists.
- The user's org is `thierno_perso`; if account selection is ambiguous, ask
  the user which account to use.
