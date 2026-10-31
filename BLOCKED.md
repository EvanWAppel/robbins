# BLOCKED — what I need from Evan

> **Fleet repo (_system D-036, D-051, D-052):** robbins's blockers live in Jira as *Needs Evan*
> tickets (component `robbins`; file with `uv run --project ~/Documents/_system sys file-blocker`);
> `sys blockers` mirrors them into the todo dashboard. Two kinds stay here: `[sec]` blockers (the
> security dashboard counts them only here) and anything Jira must not hold — rosters, secrets,
> unpublished writing. Moved 2026-10-31: EA-43 (Review the Tiresias gold set and column-doc claims), EA-44 (Verify robbins' project.toml draft), EA-46 (Decide what to do with the two stale snapshot bran).


When something needs Evan — a credential, a deploy, or a decision only he can make — add a checkbox line below with the severity (🔴 blocking / 🟡 nice-to-have), a short title, and the **specific steps a human takes to unblock it** (the action, where, any URL/path/env-var). Only open items are mirrored into the todo dashboard.

- [ ] 🟡 [sec] **Revoke the Anthropic key Railway used before 2026-10-23** — Railway → robbins → `ANTHROPIC_API_KEY` now holds a key from the dedicated `robbins` workspace ($10/month cap, $9 alert), so the old key is no longer needed by the live Ask Tiresias page. If you haven't already: in the Anthropic Console (https://console.anthropic.com/settings/keys), find the key that was set in Railway before the swap, in whatever workspace it came from (possibly your personal/default one), and revoke it. If your local `robbins/.env` still holds that old key, replace it with the `robbins` workspace key. Safe: nothing deployed references the old key any more.

