# Agent rule: You may commit+push only after you show:
1) `git status` output
2) a short list of files changed + what changed
3) the exact commit message you will use
Never push secrets (.env), never run destructive DB commands, never push unreviewed migrations.
