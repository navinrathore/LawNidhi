# Agentic Architecture & Design Patterns

This document captures the architectural decisions and agentic workflows to be used in LawNidhi, drawing upon the lessons learned from the `Data Analyst Agent` and `TowerOfHanoi` projects.

## 1. The ReAct Loop (Reasoning and Acting)
For general exploratory queries (like "How many cases are OPEN in July?"), we use a custom-built ReAct loop.
- **Safety Nets**: Always implement a strict `max_loops` threshold (e.g., 10-15 loops).
- **Execution Sandboxing**: Raw subprocess execution is highly dangerous. If Python execution is ever introduced, it MUST run within a sandboxed environment (Docker or a microVM). For LawNidhi, our agents only interact with a read-only or strictly bounded SQLite tool.

## 2. Provider Agnostic LLM Interface
Never hardcode tools into Anthropic or OpenAI specific SDKs.
- Use a unified `BaseLLMClient` interface.
- This allows the system to toggle between `Claude-3.5`, `GPT-4o`, or local open-weight models (`Qwen-2.5-72B`) seamlessly based on cost and availability.

## 3. Context Pruning
When running extensive parsing or looping, the conversation history grows quickly.
- Production agents should summarize older loops to keep context token counts low.
- For NGT cause lists, only feed the LLM small page chunks, not the entire PDF at once.

## 4. Conditional Guardrails (Avoiding the Token Tax)
Avoid forcing rigid checklists (`manage_checklist`) on frontier models unless needed. Make these guardrails conditionally configurable (`use_checklist: false`) so they can be toggled off for smarter models.
