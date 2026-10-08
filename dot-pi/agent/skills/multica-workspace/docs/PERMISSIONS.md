# Permissions Reference (workspace roles)

Three roles: `owner`, `admin`, `member`. Roles control workspace settings and team management only — day-to-day collaboration (creating issues, writing comments) is open to all members.

| Action | owner | admin | member |
|--------|-------|-------|--------|
| View & collaborate day-to-day | ✅ | ✅ | ✅ |
| Change workspace settings | ✅ | ✅ | ❌ |
| Invite an admin or member | ✅ | ✅ | ❌ |
| Change/remove an admin or member | ✅ | ✅ | ❌ |
| Grant/revoke/remove `owner` | ✅ | ❌ | ❌ |
| Delete the workspace | ✅ | ❌ | ❌ |

## Important corrections vs. the old model

- **Roles do NOT decide who can run an agent.** Each agent has its own **Access** scope (`Only me` / `Entire workspace` / `Specific people`). `owner` and `admin` **cannot bypass Access** to run agents they were not granted. There is no "assign private agent" role permission — assignment is gated by Access, not by role.
- Invitations can only grant `admin` or `member`; an `owner` must join first and be promoted by an existing `owner`.
- A workspace must keep at least one `owner` — the last owner cannot be demoted, removed, or leave.
- Role changes take effect immediately.
- Removing a member deactivates their runtimes, archives the agents bound to them, cancels unfinished runs, and clears their agent-Access grants (not restored automatically on rejoin).
- Leaving a workspace deactivates runtimes you own and archives the agents bound to them; you need a new invitation to return.

## Agent Access vs. workspace role (summary)

| Question | Decided by |
|----------|-----------|
| Can I see this agent? | ownership + admin role + Access |
| Can I modify this agent? | owner + workspace owners/admins (Access = owner only) |
| Can I run this agent? | the agent's Access scope only |
