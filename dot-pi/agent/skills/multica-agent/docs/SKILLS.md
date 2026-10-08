# Skills: Attaching Knowledge Packs

Skills are knowledge packs (SKILL.md + supporting files) that tell an agent "when you hit this kind of task, think and act like this."

## Supported sources

| Source | Command example | Notes |
|--------|------------------|-------|
| **GitHub** | `multica-agent skills add ag_123 --source github --url https://github.com/owner/repo/tree/main/skills/my-skill --i-understand-risks` | Size cap: ~1 MB per file |
| **ClawHub** | `multica-agent skills add ag_123 --source clawhub --url "my-skill@v1.2" --i-understand-risks` | Public marketplace — verify version & author |
| **Local** | `multica-agent skills add ag_123 --source local --path ./my-skill` | Requires `SKILL.md` in root directory |

## Requirements for a valid skill
- Must contain `SKILL.md` at root
- `SKILL.md` must have `name`, `version`, `description`
- Total size < 1 MB (enforced by Multica server)

> 💡 Tip: Use local skills for sensitive or experimental content. Only import from GitHub/ClawHub when you fully trust the source.
