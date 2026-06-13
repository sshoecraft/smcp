# Changelog

All notable changes to the Ask SMCP server are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-06-13

### Added
- **OpenAI `ASK_REASONING_EFFORT` knob** (`minimal`/`low`/`medium`/`high`, default unset → model default). Passed as `reasoning_effort` only for reasoning models (`gpt-5`/o-series) and only when set, so plain chat models and OpenAI-compatible backends (Grok/xAI, vLLM) never receive the param. Lower values reclaim visible-output budget.
- **`finish_reason`, `continuations`, and token usage on the success path for all three vendors.** Callers can now tell a complete answer from one truncated at the output cap. Usage keys are uniform: `prompt_tokens`, `output_tokens`, `thoughts_tokens`, `total_tokens`.
- **Bounded auto-continuation for OpenAI and Anthropic**, mirroring Gemini: on an output-cap stop (`length` / `max_tokens`) with visible text, issue a single continuation call (worst case 2 API calls per ask), gated by `ASK_AUTO_CONTINUE` (default on). No continuation is attempted when there is no visible text to continue from.

### Changed
- `ASK_AUTO_CONTINUE` now applies to all vendors (previously Gemini + OpenAI); README and credential schema updated accordingly.
- Anthropic reports `thoughts_tokens=0` and computes `total_tokens` as input + output, since the Messages API bills extended-thinking tokens inside `output_tokens` and returns no separate count or total.

### Fixed
- Anthropic no longer silently returns content truncated at `max_tokens` with no signal to the caller.
- Synced `__version__` in `__init__.py`, which had drifted to `0.1.3` while the package version advanced.

## [0.2.1]

### Changed
- Use `max_completion_tokens` instead of `max_tokens` for GPT-5 family and o-series reasoning models, which reject `max_tokens`.

## [0.2.0]

### Added
- Gemini thinking configuration (`ASK_THINKING_LEVEL`).
- Startup/runtime instrumentation.
- Auto-continue on output-cap truncation (`ASK_AUTO_CONTINUE`), initially for Gemini.

## [0.1.x]

### Added
- Initial Ask SMCP server: exposes a single external LLM provider (Gemini, OpenAI Chat-Completions, or Anthropic Messages) as one MCP `query` tool. SMCP-enabled, with credentials via the SMCP handshake or environment variables.
