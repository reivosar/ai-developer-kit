---
name: claude-api
description: Answer questions about the Claude API (Anthropic SDK), Claude Code
  CLI features, or the Agent SDK. Use when the user asks how to use the API, how
  to stream responses, what models are available, or needs help implementing an
  Anthropic SDK integration.
---

# Claude API

Answer questions and implement code involving the Claude / Anthropic API.

## Arguments

`$ARGUMENTS` is the question or task. Examples:
- "How do I stream a response with the Python SDK?"
- "What's the token limit for claude-opus-4-7?"
- "Implement a tool-use loop"

## Process

### Research questions ("how do I", "what is", "does it support")

Spawn a `claude-code-guide` subagent with the question. That agent has access
to up-to-date documentation. Return its answer directly.

### Implementation tasks

Use `/coding` with the API implementation spec. Include in the spec:
- The target language and SDK version
- The specific API feature (streaming, tool use, vision, etc.)
- Any relevant model IDs or constraints

Current model IDs (as of knowledge cutoff):
- Opus 4.7: `claude-opus-4-7`
- Sonnet 4.6: `claude-sonnet-4-6`
- Haiku 4.5: `claude-haiku-4-5-20251001`

Default to the latest capable model unless the user specifies otherwise.
