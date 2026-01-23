# AI Usage Statement

This document describes how Large Language Models (LLMs) were used during the development of this project, maintaining transparency about the development process.

## Development Phases

The application development was divided into 4 phases:

### I - Stone Age

**Description:** Initial project structure setup (approximately 5 hours of work), including:

- Implementation of the general structure for the challenge's main components
- Design of the rebalancing algorithm
- Implementation of price change event flow

**AI Usage in This Phase:**
- Low usage, only one prompt was used:
  - `docs/used_prompts/event-handler-prompt.md` for debugging a blocking issue in the implementation

### II - The Renaissance

**Description:** After reflecting on the poor quality of the previous implementation (the "5 hours guy") regarding key business logic, several underlying elements were improved before covering the key components:

- Implementation of global decimal depth configuration based on findings in Alpaca documentation (link: https://alpaca.markets/learn/fractional-shares-api)
- Addition of helper functions in utils to avoid problems with Decimal type operations
- Moved FAKE MARKET to utils as it's a utility element focused on rebalancing demonstration
- Implementation of general application configuration (settings), with configs grouped by usage context
- Addition of main logic errors in all associated modules
- Addition of UUID for tracking buy and sell operations performed with the broker
- Incorporation of PortfolioConfig schema to validate in the DTO layer all business rules associated with portfolio instantiation and avoid saturating its constructor
- Addition of validation for Stock class instantiation with errors in the respective module
- Creation of CLAUDE.MD and AGENTS.md for better context for the agent in requests

**AI Usage in This Phase:**
- Mainly in the implementation of Decimal management utility tools (utils/*)
- For such tasks, I typically spend tokens extensively asking the AI for analysis reports from different viewpoints and options analysis with tradeoffs, iterating doubts until having an understanding of various options and tradeoffs between them
- Then I would use Claude Code's planning mode and iterate

### III - Modernism

**Description:** Here I detailed the complete implementation to be performed with all technical execution details that the agent should perform. I described flows, specific modifications to be made, and used Claude Code's planning mode to identify blind spots, reviewed the plan, requested adjustments if needed, and asked it to execute the plan.

Afterwards, based on what it did, I generated cleanup modifications of comments (the AI usually adds many comments), things that aren't clear, etc.

This is how I implemented the two key business functionalities in the broker and portfolio.

**AI Usage in This Phase:**
- Primarily two prompts:
  - `docs/used_prompts/portfolio-batch-operations-prompt.md`
  - `docs/used_prompts/portfolio-rebalance-lock-prompt.md`

### IV - Post Modernism

**Description:** I used various prompts to receive suggestions for base test structures, but with my pre-indications about which business cases should be focused on in the test suite. Based on this, tests were received, adjusted, cleaned up, and iterated upon until having a test implementation that truly tests business logic and is isolated to avoid side effects.

**AI Usage in This Phase:**
- Mainly the prompts in: `docs/used_prompts/testing-prompts.md`

---

## Transparency Commitment

This project demonstrates how AI tools can be effectively used as coding assistants while maintaining human oversight and architectural decision-making. The use of AI accelerated development but all business logic decisions, architecture choices, and implementation strategies were directed by human judgment and expertise in financial software engineering.
