/**
 * Composio Integration Extension
 *
 * Bridges pi to the Composio CLI (https://composio.dev) so the agent can
 * interact with 250+ third-party apps (Gmail, Slack, GitHub, Notion,
 * Linear, Telegram, Google Calendar, ...) through structured tools.
 *
 * Tools:
 *   - composio_search       find the right action slug for a use case
 *   - composio_execute      run an action against a connected app account
 *   - composio_connections  inspect connected accounts / their status
 *
 * Requirements: `composio` CLI on PATH (v0.3.3+), logged in (`composio whoami`),
 * and app accounts linked via `composio link <app>` (OAuth, one-time).
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { Type } from "typebox";

const execFileAsync = promisify(execFile);
const MAX_BUFFER = 16 * 1024 * 1024; // 16 MiB

interface CliResult {
	ok: boolean;
	text: string;
}

async function runCli(args: string[], signal?: AbortSignal): Promise<CliResult> {
	try {
		const { stdout } = await execFileAsync("composio", args, {
			maxBuffer: MAX_BUFFER,
			signal,
		});
		return { ok: true, text: stdout.trim() };
	} catch (err: unknown) {
		const e = err as { code?: string | number; stdout?: string; stderr?: string; message?: string };
		if (e.code === "ENOENT") {
			return {
				ok: false,
				text: "The `composio` CLI is not installed or not on PATH. Install it with: pip install composio-core  (then run `composio login`).",
			};
		}
		if (e.name === "AbortError" || (e as { signal?: unknown }).signal) {
			return { ok: false, text: "composio call aborted." };
		}
		const detail = ((e.stderr || "") + "").trim() || ((e.stdout || "") + "").trim() || e.message || String(e);
		return { ok: false, text: detail.slice(0, 4000) };
	}
}

const SearchParams = Type.Object({
	query: Type.String({
		description:
			"Use case to find an action for, e.g. 'send an email', 'create a github issue', 'post a slack message'.",
	}),
	toolkits: Type.Optional(
		Type.String({
			description:
				"Comma-separated toolkit slugs to filter by (e.g. 'github,gmail'). Optional.",
		}),
	),
	limit: Type.Optional(
		Type.Number({
			description: "Max results to return (1-20, default 5).",
			default: 5,
		}),
	),
});

const ExecuteParams = Type.Object({
	slug: Type.String({
		description:
			"Action slug, e.g. GITHUB_CREATE_ISSUE, GMAIL_SEND_EMAIL, SLACK_POST_MESSAGE. Find slugs with composio_search.",
	}),
	data: Type.Optional(
		Type.Record(Type.String(), Type.Unknown(), {
			description: "Action input parameters as an object, e.g. { owner: 'acme', repo: 'app', title: 'Bug' }.",
		}),
	),
	account: Type.Optional(
		Type.String({
			description:
				"Optional connected-account selector (alias, word_id, or connected account ID) when multiple accounts of the app exist.",
		}),
	),
	dryRun: Type.Optional(
		Type.Boolean({ description: "Validate and preview the call without executing. Default false." }),
	),
	getSchema: Type.Optional(
		Type.Boolean({ description: "Print the input schema for the action without executing. Default false." }),
	),
});

const ConnectionsParams = Type.Object({});

export default function composioExtension(pi: ExtensionAPI) {
	pi.registerTool({
		name: "composio_search",
		label: "Composio: find action",
		description:
			"Find a Composio action slug for a third-party app use case (Gmail, Slack, GitHub, Notion, Linear, Telegram, etc.). Use this BEFORE composio_execute when you don't know the exact slug.",
		parameters: SearchParams,
		async execute(_toolCallId, params, signal) {
			const args = ["search", params.query];
			if (params.toolkits) args.push("--toolkits", params.toolkits);
			if (params.limit) args.push("--limit", String(params.limit));
			const res = await runCli(args, signal);
			return {
				content: [{ type: "text", text: res.ok ? res.text : `Error: ${res.text}` }],
			};
		},
	});

	pi.registerTool({
		name: "composio_execute",
		label: "Composio: execute action",
		description:
			"Execute an action on a third-party app via Composio (e.g. send an email, create a GitHub issue, post to Slack, read Notion pages). The account must already be connected (see composio_connections / composio link <app>).",
		parameters: ExecuteParams,
		async execute(_toolCallId, params, signal) {
			const args = ["execute", params.slug];
			if (params.data !== undefined && Object.keys(params.data).length > 0) {
				args.push("-d", JSON.stringify(params.data));
			}
			if (params.account) args.push("--account", params.account);
			if (params.dryRun) args.push("--dry-run");
			if (params.getSchema) args.push("--get-schema");

			const res = await runCli(args, signal);
			let text: string;
			if (res.ok) {
				text = res.text || "(no output)";
			} else {
				text = `composio execute ${params.slug} failed:\n${res.text}\n\nCommon fixes:\n- If a connection is missing/expired, run 'composio link ${params.slug.split("_")[0].toLowerCase()}' (interactive OAuth) or check 'composio connections list'.\n- Verify the slug with composio_search, and the parameters with composio_execute(slug, getSchema=true).`;
			}
			return {
				content: [{ type: "text", text }],
			};
		},
	});

	pi.registerTool({
		name: "composio_connections",
		label: "Composio: connected accounts",
		description:
			"List all third-party app accounts connected to Composio and their status (ACTIVE/EXPIRED). Use to verify an app is available before composio_execute, and to tell the user which apps still need to be linked.",
		parameters: ConnectionsParams,
		async execute(_toolCallId, _params, signal) {
			const res = await runCli(["connections", "list"], signal);
			let text: string;
			if (res.ok) {
				try {
					const data = JSON.parse(res.text) as Record<
						string,
						Array<{ status?: string; alias?: string | null; word_id?: string }>
					>;
					const lines: string[] = [];
					for (const [app, conns] of Object.entries(data)) {
						for (const c of conns) {
							lines.push(`${c.status || "?"}\t${app}\t${c.alias || c.word_id || "?"}`);
						}
					}
					text = lines.length ? lines.join("\n") : "No connected accounts. Run `composio link <app>` to connect one.";
				} catch {
					text = res.text || "(no output)";
				}
			} else {
				text = `Error: ${res.text}`;
			}
			return { content: [{ type: "text", text }] };
		},
	});
}
