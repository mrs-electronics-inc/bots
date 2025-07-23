# Bots 🤖

This repository contains various bots that assist us in our software development process.

## Code Review 🧐💻

The initial goal for this bot is to inspect a `git` repo and write a `.bots/summary.md` file based on the diffs with the main branch.

You can test the current iteration of the bot locally using the following:
```
docker run --pull always -it -v .:/repo ghcr.io/mrs-electronics-inc/bots/code-review:main
```

This will open an interactive `bash` shell with access to `git` and `aider`.

Soon we should have a script built that automatically generates the `.bots/summary.md` file.
