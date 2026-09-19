# Agent Instructions

## Session Initialization & Context Loading

At the beginning of any AI agent session, you must **systematically** and **imperatively** read and take into account the following files:

- `01_context/documentation/project_structure_guidelines.md`
- `01_context/rules.md`

Additionally, if any other files or sub-files within `01_context/` (e.g., `01_context/glossary.md`, `01_context/adr/`, etc.) seem pertinent given the specific task at hand, they should also be read and taken into account from the beginning.

### Exception

You may skip reading these files only if you are asked a simple question for which the full context to answer is **confidently** already available in the immediate conversation context.
