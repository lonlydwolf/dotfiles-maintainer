# Case study: a memory companion for dotfiles

## Motivation and ownership

I wanted AI help maintaining my dotfiles and remembering why I had made particular configuration decisions. I owned the whole project, from deciding what the assistant should be able to ask for to implementing the MCP server, memory integration, CLI, tests, and documentation.

The hardest part was deciding which tools the assistant actually needed. The original scope grew to include baseline information, change rationale, troubleshooting, roadmap ideas, trials, lifecycle changes, and session handoff. That made tool selection a product-design question as much as an implementation question: which recurring user task deserved a dedicated interface?

## What I built

The prototype exposes typed MCP tools through the official Python SDK's FastMCP server. Tool modules call a shared memory wrapper; mem0 handles semantic memory backed by Qdrant, with sentence-transformer embeddings and a configurable internal LLM. Git/Jujutsu helpers supply working-tree status and history. A Typer CLI provides manual access to parts of the system.

Separating the protocol adapters, tools, memory service, and VCS utilities made individual components easier to inspect and test. The repository includes mocked service tests and real temporary-repository tests, and the January 2026 release had passing CI across Python 3.10–3.13. Those are concrete delivery outcomes, not evidence of sustained adoption or production readiness.

The implemented tools record information supplied by an assistant and retrieve potentially relevant memories. They do not independently verify the assistant's rationale, manage deployed dotfiles, or make semantic search results authoritative state.

## Why I retired it

I no longer use the server. In my own workflow, asking a model to inspect my dotfiles and Git history has proved sufficient for the help I need. Keeping a separate memory service, provider configuration, and dependency stack therefore has little continuing value for me.

That experience does not mean a model can recover intent that was never written down, or that persistent memory has no value elsewhere. It means this implementation no longer earns its maintenance cost for my use case. Retiring it preserves the learning without implying an ongoing product commitment.

## What the later review showed

The October 2026 closeout review examined the implementation and ran synthetic checks in temporary repositories. These are later findings, separate from my original motivation and development experience:

- Environment configuration and documentation diverged: the generic key needs the `DOTFILES_` prefix, while provider autodetection overwrites explicit model selection.
- The status tool follows process working directory. A separate clean server checkout can be checked while the actual dotfiles repository is dirty; Jujutsu's human-readable clean output is also misclassified.
- Regex redaction does not remove complete private-key blocks or all structured secret values. Metadata is not scrubbed.
- Some parameters imply deterministic filtering that the semantic implementation does not enforce. An empty memory result can also hide an already-observed status result.

The checks used synthetic data, real Git/Jujutsu and Pydantic settings, and substituted provider/memory objects. They did not exercise a live LLM, a full embedding pipeline, or the whole current dependency suite. Historical CI and these focused checks answer different questions.

## Engineering lessons I would carry forward

**Start from one recurring task.** A narrower first version could record and retrieve configuration rationale. Baselines, trials, roadmaps, and other tools should justify their own interface and maintenance cost through actual use.

**Keep authoritative records separate from semantic retrieval.** Store the original rationale with a stable reference to a change. Treat extracted facts and search results as an aid to finding that record. Status, dates, and categories need deterministic fields and filtering when an interface promises them.

**Test the boundary the user actually encounters.** Model tests and mocked happy paths are useful, but they missed environment-variable names, installation versus target directory, clean Jujutsu output, and empty memory results. A small set of end-to-end acceptance cases would have caught more meaningful failures than adding more tools.

**Let independent operations fail independently.** A known working-tree status should remain available when memory persistence fails. A convenience redactor should not be described as a security guarantee, and provider configuration should preserve explicit user choices.

**Evaluate the simpler workflow.** For a future applied-AI project, I would compare a small prototype with the existing workflow before committing to a broad tool suite. Here, inspecting files and history became sufficient for my needs. Knowing when to stop is part of owning the result.

The project remains useful as a record of learning backend boundaries, external-service integration, and AI tool design. Its next version is not currently planned.
