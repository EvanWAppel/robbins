# BLOCKED — what I need from Evan

Nothing blocked right now. When something needs Evan — a credential, a deploy, or a decision only he can make — add a checkbox line below with the severity (🔴 blocking / 🟡 nice-to-have), a short title, and the **specific steps a human takes to unblock it** (the action, where, any URL/path/env-var). Only open items are mirrored into the todo dashboard.

- [ ] 🔴 **Check which Anthropic key robbins' live deploy uses, then give it a dedicated one** — the old "Ask the Data" page called Claude with `ANTHROPIC_API_KEY` described as "the user's own" key, on a public Railway app. In Railway → robbins → Variables, check `ANTHROPIC_API_KEY`; if it is your personal/default key, rotate it in the Anthropic Console (https://console.anthropic.com/settings/keys). Then create a separate workspace (e.g. `tiresias-robbins`) with a monthly spend limit + alert (Elvis uses $10), mint a key there, set it in Railway and in `robbins/.env`, and tell Claude it is not your personal/default key. Until then, unset the variable: the new page then shows a "needs a key" notice.
- [ ] 🟡 **Review the Tiresias gold set and column-doc claims** — skim `evals/tiresias_gold.yaml` (25 drafted questions) and check the 5 claims in `TIRESIAS.md` → "Column-doc claims to check against the data".
- [ ] 🔴 **Approve merging the `tiresias` PR** (merge = deploy on Railway). If Railway still holds a personal key, fix that first (item above): the merged page would use whatever key is set.

