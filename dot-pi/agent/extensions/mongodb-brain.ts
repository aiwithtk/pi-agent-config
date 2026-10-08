/**
 * mongodb-brain — mémoire long terme MongoDB pour pi.
 *
 * 1. Injecte le digest de la mémoire (db `brain`) au début de chaque session, puis le rafraîchit
 *    au bout de BRAIN_DIGEST_TTL minutes (défaut 30).
 * 2. Trace automatiquement chaque session dans la collection `sessions` (aucun appel modèle) :
 *    dossier, modèle, durée, échanges, outils utilisés, fichiers touchés, premier/dernier message.
 * 3. Expose l'outil `brain` (recherche, écriture de faits/décisions/leçons, tâches…).
 *
 * Tout passe par le CLI ~/.pi/agent/bin/brain (voir skill "brain"). Désactivable avec BRAIN_DISABLE=1.
 */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { homedir } from "node:os";

const exec = promisify(execFile);
const BRAIN = `${homedir()}/.pi/agent/bin/brain`;
const TTL_MS = (Number(process.env.BRAIN_DIGEST_TTL) || 30) * 60 * 1000;
const MAX_CHARS = Number(process.env.BRAIN_DIGEST_MAX) || 16000;
const FLUSH_EVERY_MS = (Number(process.env.BRAIN_TRACE_EVERY) || 120) * 1000;
const DISABLED = process.env.BRAIN_DISABLE === "1";

async function runBrain(args: string[], timeout = 20000): Promise<string> {
  const { stdout } = await exec(BRAIN, args, { timeout, maxBuffer: 4 * 1024 * 1024 });
  return stdout.trim();
}

type Trace = {
  sessionId: string;
  cwd: string;
  model?: string;
  provider?: string;
  reason?: string;
  startedAt: string;
  turns: number;
  tools: Record<string, number>;
  files: Set<string>;
  firstPrompt?: string;
  lastPrompt?: string;
};

export default function (pi: ExtensionAPI) {
  if (DISABLED) return;

  let lastDigestAt = 0;
  let digestInflight: Promise<string | null> | null = null;
  let digestWarned = false;

  let trace: Trace | null = null;
  let lastFlushAt = 0;
  let flushes = 0;
  let ingestStarted = false;

  const loadDigest = (): Promise<string | null> => {
    if (!digestInflight) {
      digestInflight = runBrain(["digest", "--max", String(MAX_CHARS)]).catch(() => null);
      digestInflight.finally(() => { digestInflight = null; });
    }
    return digestInflight;
  };

  // ---------------------------------------------------------------- trace
  const traceDoc = () => {
    if (!trace) return null;
    const tools = Object.entries(trace.tools)
      .sort((a, b) => b[1] - a[1])
      .map(([k, v]) => `${k}:${v}`)
      .join(", ");
    const started = new Date(trace.startedAt).getTime();
    return {
      sessionId: trace.sessionId,
      cwd: trace.cwd,
      model: trace.model,
      provider: trace.provider,
      reason: trace.reason,
      startedAt: trace.startedAt,
      endedAt: new Date().toISOString(),
      durationMs: Date.now() - started,
      turns: trace.turns,
      tools,
      files: [...trace.files].slice(0, 30),
      firstPrompt: trace.firstPrompt?.slice(0, 200),
      lastPrompt: trace.lastPrompt?.slice(0, 120),
    };
  };

  const flush = async (force = false) => {
    if (!trace) return;
    if (!force && Date.now() - lastFlushAt < FLUSH_EVERY_MS) return;
    if (trace.turns === 0 && Object.keys(trace.tools).length === 0) return;
    const doc = traceDoc();
    if (!doc) return;
    lastFlushAt = Date.now();
    flushes++;
    try {
      await runBrain(["put", "sessions", JSON.stringify(doc)], 15000);
    } catch {
      /* la trace ne doit jamais faire échouer la session */
    }
  };

  pi.on("session_start", (event: any, ctx: any) => {
    lastDigestAt = 0;
    digestWarned = false;
    // ingestion incrémentale du contexte (les .jsonl de la session précédente), en tâche de fond
    if (!ingestStarted) {
      ingestStarted = true;
      runBrain(["ingest"], 120000).catch(() => {});
    }
    let sessionId = "";
    try { sessionId = ctx.sessionManager.getSessionId(); } catch {}
    const model = ctx.model as any;
    trace = {
      sessionId: sessionId || `ephemeral-${Date.now()}`,
      cwd: ctx.cwd || process.cwd(),
      model: model?.id || model?.name,
      provider: model?.provider || model?.providerId,
      reason: event?.reason,
      startedAt: new Date().toISOString(),
      turns: 0,
      tools: {},
      files: new Set<string>(),
    };
    lastFlushAt = 0;
    flushes = 0;
  });

  pi.on("session_shutdown", async () => {
    await flush(true);
  });

  pi.on("agent_settled", async () => {
    await flush(false);
  });

  pi.on("tool_call", (event: any) => {
    if (!trace) return;
    const name = String(event?.toolName || "?");
    trace.tools[name] = (trace.tools[name] || 0) + 1;
    const input = event?.input || {};
    const path = input.path || input.file_path || input.filePath;
    if (typeof path === "string") trace.files.add(path);
  });

  pi.on("before_agent_start", async (event: any, ctx: any) => {
    if (trace) {
      trace.turns++;
      const prompt = typeof event?.prompt === "string" ? event.prompt : "";
      if (prompt && !trace.firstPrompt) trace.firstPrompt = prompt;
      if (prompt) trace.lastPrompt = prompt;
    }

    const fresh = Date.now() - lastDigestAt < TTL_MS;
    if (lastDigestAt !== 0 && fresh) return;
    const digest = await loadDigest();
    if (!digest) {
      if (!digestWarned) {
        digestWarned = true;
        ctx.ui.notify("brain: mémoire MongoDB injoignable (digest ignoré)", "warning");
      }
      return;
    }
    if (digest.startsWith("(cerveau vide")) return;
    lastDigestAt = Date.now();
    return {
      message: {
        customType: "brain-digest",
        display: false,
        content: [
          '<memoire-long-terme source="mongodb:brain">',
          "Contexte durable issu des sessions précédentes. Traite-le comme des notes de toi-même :",
          "ne le récite pas, ne le résume pas à l'utilisateur, utilise-le. Si une info contredit",
          "ce que dit l'utilisateur maintenant, c'est l'utilisateur qui a raison (et mets la mémoire à jour).",
          "",
          digest,
          "</memoire-long-terme>",
        ].join("\n"),
      },
    };
  });

  // ---------------------------------------------------------------- outil brain
  pi.registerTool({
    name: "brain",
    label: "Brain (mémoire MongoDB)",
    description:
      "Mémoire long terme MongoDB. search: retrouver un contexte (inclut l'historique complet des conversations via `transcripts`) ; " +
      "put: mémoriser un fait/projet/personne/snippet (upsert) ; " +
      "add: consigner tâche/décision/leçon/journal ; ls/get: consulter ; done/rm: clore ou supprimer ; " +
      "ingest: (re)charger le contexte des sessions pi ; digest: tout le contexte ; stats/schema.",
    parameters: Type.Object({
      action: Type.Union(
        [
          Type.Literal("search"), Type.Literal("put"), Type.Literal("add"), Type.Literal("ls"),
          Type.Literal("get"), Type.Literal("done"), Type.Literal("rm"), Type.Literal("digest"),
          Type.Literal("ingest"), Type.Literal("stats"), Type.Literal("schema"),
        ],
        { description: "Opération à effectuer" },
      ),
      collection: Type.Optional(
        Type.Union(
          [
            Type.Literal("facts"), Type.Literal("projects"), Type.Literal("people"), Type.Literal("tasks"),
            Type.Literal("decisions"), Type.Literal("lessons"), Type.Literal("journal"),
            Type.Literal("sessions"), Type.Literal("transcripts"), Type.Literal("snippets"),
          ],
          { description: "Collection cible (put/add/ls/get/rm/search)" },
        ),
      ),
      query: Type.Optional(Type.String({ description: "Texte recherché (action search) ou id de document (get/done/rm)" })),
      doc: Type.Optional(Type.Record(Type.String(), Type.Any(), { description: "Document JSON à écrire (put/add)" })),
      filter: Type.Optional(Type.Record(Type.String(), Type.Any(), { description: "Filtre MongoDB (action ls)" })),
      limit: Type.Optional(Type.Number({ description: "Nombre max de résultats (défaut 8 pour search, 25 pour ls)" })),
    }),
    async execute(_id, params) {
      const { action, collection, query, doc, filter, limit } = params as {
        action: string; collection?: string; query?: string;
        doc?: Record<string, unknown>; filter?: Record<string, unknown>; limit?: number;
      };
      const args: string[] = [];
      switch (action) {
        case "search":
          if (!query) return fail("search nécessite `query`");
          args.push("search", query, "--limit", String(limit ?? 8));
          if (collection) args.push("--collection", collection);
          break;
        case "put":
        case "add":
          if (!collection || !doc) return fail(`${action} nécessite \`collection\` et \`doc\``);
          args.push(action, collection, JSON.stringify(doc));
          break;
        case "ls":
          if (!collection) return fail("ls nécessite `collection`");
          args.push("ls", collection, "--limit", String(limit ?? 25));
          if (filter) args.push("--filter", JSON.stringify(filter));
          break;
        case "get":
        case "rm":
          if (!collection || !query) return fail(`${action} nécessite \`collection\` et \`query\` (id)`);
          args.push(action, collection, query);
          break;
        case "done":
          if (!query) return fail("done nécessite `query` (id de la tâche)");
          args.push("done", query);
          break;
        case "digest":
          args.push("digest", "--max", String(MAX_CHARS));
          break;
        case "ingest":
          args.push("ingest");
          break;
        case "stats":
        case "schema":
          args.push(action);
          break;
        default:
          return fail(`action inconnue: ${action}`);
      }
      try {
        const text = await runBrain(args, 30000);
        return { content: [{ type: "text", text: text || "(vide)" }], details: { action } };
      } catch (e) {
        return fail(`brain ${action} a échoué: ${(e as Error).message.split("\n")[0]}`);
      }
    },
  });
}

function fail(message: string) {
  return { content: [{ type: "text" as const, text: `Erreur: ${message}` }], details: {}, isError: true };
}
