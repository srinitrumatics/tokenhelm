# Recommended GitHub Discussions Categories

Discussions categories are configured in the GitHub UI (*Settings → General → Features →
Discussions → Set up*, then *Discussions → Categories*). Apply the set below. The **Format**
column maps to GitHub's category formats: *Announcement* (maintainers post, others comment),
*Q&A* (questions with markable answers), or *Open* (threaded discussion).

| Category | Format | Emoji | Description |
|----------|--------|-------|-------------|
| **Announcements** | Announcement | 📣 | Releases and important project news from the maintainers. |
| **General** | Open | 💬 | Anything about TokenHelm that doesn't fit another category. |
| **Q&A** | Q&A | ❓ | Usage and how-to questions. Mark a reply as the answer when resolved. |
| **Ideas** | Open | 💡 | Propose and discuss features before opening a tracked issue. |
| **Show and Tell** | Open | 🙌 | Share what you built with TokenHelm — dashboards, integrations, patterns. |
| **Integrations** | Open | 🔌 | Custom adapters, loggers, storage backends, and framework integrations. |
| **Roadmap** | Announcement | 🗺️ | Roadmap updates and direction (see `ROADMAP.md`); discussion in comments. |

## Routing

- `.github/ISSUE_TEMPLATE/config.yml` already points "Question / Usage help" to Discussions —
  keep it aimed at **Q&A**.
- Encourage **Ideas** for feature brainstorming; promote mature ideas to a tracked
  `feature_request` issue.
- Use **Integrations** to collect community adapters/sinks that may graduate into the library
  or a contrib list.

## Suggested pinned posts

1. **Welcome & how to get help** (General) — links to README, docs, SUPPORT.md.
2. **Roadmap overview** (Roadmap) — summary of `ROADMAP.md` with status.
3. **Share your integrations** (Integrations) — call for community adapters/sinks.
