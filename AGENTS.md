# 🎮 AGENTS.md - CarePathAI

An AI system that ingests healthcare-style data and generates personalized care guidance, summaries, and routing recommendations using RAG and multi-step orchestration.


## 🤖 DELEGATE OR DIE!

**YOU ARE NOT THE EXPERT. DELEGATE EVERYTHING.**

- **NEVER** write code yourself - use the `task` tool with appropriate subagent
- **ALWAYS** start with Project Manager for complex tasks
- **ALWAYS** scan `./memory/` first before any task
- **ONLY** act when explicitly told to do something directly
- **FAILURE** to delegate properly will result in broken code and wasted time

## 🤖 Agent Delegation - USE THESE FOR EVERYTHING

- **Project Manager:** Task coordination, workflow management, delegation (USE THIS FIRST)
- **Architect:** System design, tech choices, architecture decisions
- **Developer:** Feature implementation, bug fixes, code logic
- **UI Engineer:** Component styling, interactions, accessibility
- **Test Engineer:** Test authoring, coverage, quality assurance
- **Documentation:** Docs, README updates, API references
- **Content Writer:** Blog posts, SEO optimization, project showcases, portfolio content
- **DevOps Engineer:** GitHub Actions, GitHub Pages, deployment optimization
- **Game Developer:** Web Audio API, Canvas rendering, 8-bit game development

**Examples:**

- `task(description="Coordinate project setup", prompt="Analyze requirements and delegate Astro project initialization to appropriate agents", subagent_type="project-manager")`
- `task(description="Build portfolio layout", prompt="Create responsive GameBoy-styled portfolio with Tokyo Night theme", subagent_type="ui-engineer")`
- `task(description="Fix build error", prompt="Debug and resolve Astro build failure", subagent_type="developer")`
- `task(description="Add search functionality", prompt="Implement Pagefind search with custom UI", subagent_type="developer")`
- `task(description="Update README", prompt="Document new features and installation steps", subagent_type="documentation")`
- `task(description="Write blog post", prompt="Create SEO-optimized blog post about recent project", subagent_type="content-writer")`
- `task(description="Setup GitHub Pages", prompt="Configure username.github.io deployment with GitHub Actions", subagent_type="devops")`
- `task(description="Create mini game", prompt="Build Code Runner game with Web Audio API and Canvas", subagent_type="game-developer")`

## Commands
- put examples here

## 🎨 Code Style

- <placeholder>

## 📚 DOCUMENTATION MANDATE

**ALWAYS** delegate to Documentation agent after ANY task completion:

- `task(description="Update docs", prompt="Update README/API docs for recent changes", subagent_type="documentation")`
- **NO EXCEPTIONS** - Documentation updates are non-negotiable
- **MANDATORY** for all feature implementations, bug fixes, architectural changes

## 🧠 Memory Protocol (Context Retention)

- **Never Forget:** History matters. Don't repeat mistakes or re-litigate decisions.
- **Write:** When you solve a tricky bug, make an architectural pivot, or lock in a tech stack decision:
  - Create a concise file in `./memory/` (e.g., `001-auth-pattern.md`, `002-fix-race-condition.md`).
  - **Format:** Context ➡️ Decision ➡️ Outcome.
- **Read:** Start **EVERY** task by scanning `./memory/` for relevant context.
