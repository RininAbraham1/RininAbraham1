# Session summary: DeepSpace build exercise ("Cited")

**Deadline:** Saturday, November 21, 2026, 11:59 PM ET
**Branch:** `claude/deepspace-build-exercise-yg40ah` (pushed, commit `be7166a`)
**App folder:** `cited/`

---

## 1. The task

Build and deploy a full-stack app on DeepSpace (`npx deepspace` → `<name>.app.space`), then submit:
- the live URL
- the repository
- a short writeup: what was built, which integrations were used, the main tradeoff, what the agent did, and what you verified yourself

The bar is a focused, finished app with real technical depth and roughly 3+ integrations. A basic habit tracker isn't enough.

## 2. Decisions you made

| Question | Your answer |
| --- | --- |
| Which app? | **Cited: live trivia where every answer is sourced** (picked over "Rally" group planner and "Claim Court" fact-check) |
| How to deploy? | **Decide later** |
| Design | The first version "looks very generated, even the palette"; maybe add a mascot |
| Figma | You want Figma connected for the redesign |

## 3. What Cited is

A host types any topic. The app pulls Wikipedia articles, Claude writes multiple-choice questions, and **each question must quote a sentence that appears word for word in the article**. If it doesn't, the question is thrown out. Friends join with a 5-letter code and answer live against a timer. Each reveal shows the exact source sentence and a link to the article.

### DeepSpace pieces used
- **Records + permissions (RBAC):** live game state. The answer key (`question_bank`) is unreadable for every role, including the host and the app owner. Players see only their own answers, and browsers can't write any game data directly.
- **Server actions:** every move (`createGame`, `joinGame`, `advance`, `submitAnswer`, `reveal`, `speakQuestion`), checked against the verified user.
- **Background job:** question generation (20–60 s).
- **Presence:** shows who has the room open.
- **Integrations:** `wikipedia` (source articles), `anthropic` (question writing), `elevenlabs` (optional host-only "read questions aloud").
- **Left out on purpose:** AI chat (it would be a cheating tool), payments, file uploads, email, web search, collaborative editing.

### Main tradeoff
**Strict grounding over coverage and speed.** Requiring a verbatim, machine-checked quote throws away some good questions and can fail on thin topics. In exchange, no made-up fact can reach players.

### Security fix found in the scaffold
The scaffold's `/api/integrations/*` route let any signed-in user call any integration (including Claude) billed to the app owner. Cited now blocks it (403) unless an integration is explicitly marked `browser: true`. None are.

## 4. What was verified (by the agent)
- TypeScript, lint and production build pass, and the Worker bundles.
- **23 unit tests** pass: the quote check, HTML extraction, scoring, shuffling, join codes.
- **41 server-rule checks** pass against the real Worker running locally (`wrangler dev`), with a mock standing in for DeepSpace auth and integrations.
- **Mutation check:** making the answer key readable caused the test to fail (5 rows leaked), which proves the test isn't passing vacuously.
- **Three-browser UI run** (host, desktop player, phone player): a full game with no console errors, screenshots reviewed.
- One flaky harness run was traced to leftover processes from an earlier run. Cleanup was fixed and two back-to-back runs then passed.
- Reproduce with: `bash cited/e2e-local/run.sh` (set `PW_CHROMIUM_PATH` if needed).

**Not verified yet:** real Wikipedia/Claude output, real Google/GitHub sign-in, and the deployed app.

## 5. Environment changes made
- Created a personal cloud environment **"RininAbraham1 (DeepSpace)"** that allows DeepSpace hosts (docs, auth, API, deploy workers).
- Later added `mcp.figma.com` to it so Figma can connect.

## 6. Open items

### Deploy (needs your DeepSpace login: GitHub or Google sign-in, which needs a browser)
⚠️ The first deploy from a GitHub clone **permanently** ties the app's source to that repo. Deploying from `RininAbraham1/RininAbraham1` (your profile repo) would lock it there. Recommended: copy `cited/` into its own repo (e.g. `RininAbraham1/cited`) first.

```bash
cd cited
npm install
npx deepspace auth login
npx deepspace app init        # registers the app id (wrangler.toml has a placeholder)
git add wrangler.toml && git commit -m "Register app id"
npx deepspace deploy
```
Then play one real game and check the logs (`npx deepspace logs`).

### Redesign: done (second pass, "zine")
- Electric ultramarine stage with a halftone dot screen; cream sticker-cards with thick ink outlines and hard offset shadows; four highlighter answer colours (A yellow, B pink, C green, D cyan).
- Type: Lilita One (outlined display titles), Nunito (body), Space Mono (receipts).
- Landing: scrolling yellow marquee, the mascot surrounded by floating answer stickers, and "how it works" told as a till receipt (replaces the numbered 1-4 cards).
- Game: big countdown sticker, answer tiles that tilt when you lock in, a slapped-on "Correct! / Nope! / Too slow!" stamp, the source quote on a torn-edge receipt, and a podium for final scores.
- Mascot: the footnote asterisk (`src/components/Mascot.tsx`) with moods idle / think / happy / sad / wow / cheer.
- Checks: type-check, lint, 26 unit tests, all server-rule checks, three-browser UI run with no console errors. `SHOTS_OUT=<dir> bash e2e-local/run.sh` keeps screenshots.

### Figma
- The connector sign-in never worked in cloud sessions. Instead, a Figma personal access token is saved on the "RininAbraham1 (DeepSpace)" environment for `api.figma.com` (read files, export frames, comments). No Figma file was used for this redesign.

### Writeup
`cited/README.md` has the draft (what was built, integrations, tradeoff, verification, next steps). Write the **"what I verified myself"** part in your own words after testing the live app.

## 7. What I'd do next (from the README)
- A server-driven question timer, so a reveal happens even if every tab is closed
- Clock-skew correction for countdowns
- A second-pass check that the quote actually supports the marked answer
- Spectator / TV mode and reconnect polish
- A daily spend cap across all users
