# ADR 0003 - UI Choice: Blazor Server

## Context

CarePath AI must display patient data and AI outputs while minimizing risk of PHI exposure. Choices included Blazor Server, Blazor WASM, and a React frontend.

## Decision

Use Blazor Server for the UI. The server-side rendering keeps PHI within the server boundary, simplifies authentication, and allows leveraging C# end-to-end for UI logic.

## Consequences

- Pros:
  - Simplifies PHI handling and session state
  - Demonstrates strong C#/.NET expertise to hiring managers
  - Faster to implement server-side features (SignalR, live updates)

- Cons:
  - Less scalable than WASM for massive public traffic (fine for a portfolio prototype)
  - Ties UI to .NET runtime on the server

## Status

Accepted

## Date

2025-12-22
