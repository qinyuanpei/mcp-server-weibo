---
name: weibo-personality
description: Generate a horoscope-style personality report for a Weibo user. Fetch the user's profile and recent posts with weibo-cli, then act as the LLM yourself - apply the bundled prompt template and deliver a Chinese JSON report plus a readable summary. Use when the user asks to analyze a Weibo personality, generate a Weibo profile report or personality analysis, or provides a Weibo UID/name for personality analysis.
---

# Weibo Personality Report

Turn a Weibo user's public profile and recent posts into an entertainment-grade personality report: strengths, weaknesses, love/money/health predictions, pickup lines, roast, and more. **You are the LLM** - no API key, no backend service. Data comes from the Weibo CLI, reasoning comes from you.

## Prerequisites

- `weibo-cli` installed and working. Install and command basics are in the [Weibo CLI skill](../weibo-cli/SKILL.md).
- Read both reference files before generating:
  - [references/prompt-template.md](references/prompt-template.md) - the prompt to follow, with fill-in slots
  - [references/output-schema.md](references/output-schema.md) - exact JSON keys and field rules

## Workflow

1. **Resolve the UID.** If the user gives a nickname instead of a UID, find it with `weibo-cli users "<name>" -n 5`. Verify by description and follower count; confirm with the user when ambiguous.
2. **Fetch the profile.**

   ```bash
   weibo-cli profile <uid>
   ```

3. **Fetch posts.**

   ```bash
   weibo-cli feeds <uid> -n 50 --no-include-pics
   ```

   - Prefer each item's `raw_text`; otherwise strip HTML tags from `text`.
   - Known limit: guest sessions return only the ~10 most recent posts. For a deeper report, ask the user to run `weibo-cli login` (QR scan), then retry with `-n 50`.
   - If the user asks for a time window (e.g. last six months), drop older posts after fetching and say how many posts survived.
4. **Generate the report.** Fill the template's `profile` and `tweets` slots with the fetched data, follow the output schema exactly, and write all generated content in Chinese.
   - `name`, `avatar_hd`, `description`, `profile_url`, `follow_count`, `followers_count` must be copied from the fetched profile. Never invent them.
5. **Deliver.** Present a readable formatted report first. Offer the raw JSON as a follow-up (save to file or inline) rather than dumping it by default.

## Guardrails

- This is horoscope-style entertainment, not a psychological assessment. Say so when delivering the report.
- Only analyze public accounts. Refuse locked/private accounts.
- The roast should be edgy and witty about the persona's expressed traits - never slurs, never attacks on protected characteristics.
- Ground every claim in the fetched posts. If the sample is small (fewer than ~15 posts), say so and note the report is based on a thin sample.
