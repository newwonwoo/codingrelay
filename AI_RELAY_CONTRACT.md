# AI Relay Contract

## Core Rule

This repository uses a bidirectional AI relay workflow.

## Agent Roles

- Current Agent: the model currently modifying code.
- Next Agent: the model expected to continue work.
- Receiving Agent: the model that checks whether it can accept the Baton.
- Orchestrator: the controller that validates state and decides next action.

## Mandatory Flow

1. Understand the task.
2. Make the smallest safe change.
3. Record changed files.
4. Provide evidence.
5. Run self-verification.
6. Identify six-month failure risks.
7. Prepare Baton.
8. Do not hand off if BLOCK conditions remain.

## Forbidden

- Do not hide failed tests.
- Do not claim completion without evidence.
- Do not rewrite large areas unless explicitly requested.
- Do not remove previous Agent decisions without explaining why.
- Do not include secrets or credentials in Baton.

## Handoff Rule

No handoff without evidence.
