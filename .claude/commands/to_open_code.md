---
description: Transform a claude code config to a Opencode config
argument-hint: [aditional_context]
allowed-tools: AskUserQuestion, Task, Bash, Read, Write, Edit, Grep, Glob, TodoWrite
model: inherit
---


Queiro que me ayudes a trasnformar mi config de claude code a su simil de opencode

Debes de convertir a opencode todo lo que está aquí en este folder en los subfolders:

agents, commands, skills, tools (se mencionar tools de claude code a las propias de OpenCode)

Debes de convertirme tantos los subagents, commands y skills de claude code a opencode.

Debes de generarme un folder nuevo con todos los archivos ya convertidos al estandar que implica opencode.

Te dejaré la documentación de opencode para que puedas hacer la transformación.

El usuario ha dado como contexto:

**"$ARGUMENTS"**

Cualqueir duda que tengas, házmelo saber con AskUserQuestion.


# Agents

Agents
Configure and use specialized agents.

Agents are specialized AI assistants that can be configured for specific tasks and workflows. They allow you to create focused tools with custom prompts, models, and tool access.

Tip

Use the plan agent to analyze code and review suggestions without making any code changes.

You can switch between agents during a session or invoke them with the @ mention.

Types
There are two types of agents in OpenCode; primary agents and subagents.

Primary agents
Primary agents are the main assistants you interact with directly. You can cycle through them using the Tab key, or your configured switch_agent keybind. These agents handle your main conversation. Tool access is configured via permissions — for example, Build has all tools enabled while Plan is restricted.

Tip

You can use the Tab key to switch between primary agents during a session.

OpenCode comes with two built-in primary agents, Build and Plan. We’ll look at these below.

Subagents
Subagents are specialized assistants that primary agents can invoke for specific tasks. You can also manually invoke them by @ mentioning them in your messages.

OpenCode comes with two built-in subagents, General and Explore. We’ll look at this below.

Built-in
OpenCode comes with two built-in primary agents and two built-in subagents.

Build
Mode: primary

Build is the default primary agent with all tools enabled. This is the standard agent for development work where you need full access to file operations and system commands.

Plan
Mode: primary

A restricted agent designed for planning and analysis. We use a permission system to give you more control and prevent unintended changes. By default, all of the following are set to ask:

file edits: All writes, patches, and edits
bash: All bash commands
This agent is useful when you want the LLM to analyze code, suggest changes, or create plans without making any actual modifications to your codebase.

General
Mode: subagent

A general-purpose agent for researching complex questions and executing multi-step tasks. Has full tool access (except todo), so it can make file changes when needed. Use this to run multiple units of work in parallel.

Explore
Mode: subagent

A fast, read-only agent for exploring codebases. Cannot modify files. Use this when you need to quickly find files by patterns, search code for keywords, or answer questions about the codebase.

Usage
For primary agents, use the Tab key to cycle through them during a session. You can also use your configured switch_agent keybind.

Subagents can be invoked:

Automatically by primary agents for specialized tasks based on their descriptions.

Manually by @ mentioning a subagent in your message. For example.

@general help me search for this function

Navigation between sessions: When subagents create their own child sessions, you can navigate between the parent session and all child sessions using:

<Leader>+Right (or your configured session_child_cycle keybind) to cycle forward through parent → child1 → child2 → … → parent
<Leader>+Left (or your configured session_child_cycle_reverse keybind) to cycle backward through parent ← child1 ← child2 ← … ← parent
This allows you to seamlessly switch between the main conversation and specialized subagent work.

Configure
You can customize the built-in agents or create your own through configuration. Agents can be configured in two ways:

JSON
Configure agents in your opencode.json config file:

opencode.json
{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "build": {
      "mode": "primary",
      "model": "anthropic/claude-sonnet-4-20250514",
      "prompt": "{file:./prompts/build.txt}",
      "tools": {
        "write": true,
        "edit": true,
        "bash": true
      }
    },
    "plan": {
      "mode": "primary",
      "model": "anthropic/claude-haiku-4-20250514",
      "tools": {
        "write": false,
        "edit": false,
        "bash": false
      }
    },
    "code-reviewer": {
      "description": "Reviews code for best practices and potential issues",
      "mode": "subagent",
      "model": "anthropic/claude-sonnet-4-20250514",
      "prompt": "You are a code reviewer. Focus on security, performance, and maintainability.",
      "tools": {
        "write": false,
        "edit": false
      }
    }
  }
}

Markdown
You can also define agents using markdown files. Place them in:

Global: ~/.config/opencode/agents/
Per-project: .opencode/agents/
~/.config/opencode/agents/review.md
---
description: Reviews code for quality and best practices
mode: subagent
model: anthropic/claude-sonnet-4-20250514
temperature: 0.1
tools:
  write: false
  edit: false
  bash: false
---

You are in code review mode. Focus on:

- Code quality and best practices
- Potential bugs and edge cases
- Performance implications
- Security considerations

Provide constructive feedback without making direct changes.

The markdown file name becomes the agent name. For example, review.md creates a review agent.

Options
Let’s look at these configuration options in detail.

Description
Use the description option to provide a brief description of what the agent does and when to use it.

opencode.json
{
  "agent": {
    "review": {
      "description": "Reviews code for best practices and potential issues"
    }
  }
}

This is a required config option.

Temperature
Control the randomness and creativity of the LLM’s responses with the temperature config.

Lower values make responses more focused and deterministic, while higher values increase creativity and variability.

opencode.json
{
  "agent": {
    "plan": {
      "temperature": 0.1
    },
    "creative": {
      "temperature": 0.8
    }
  }
}

Temperature values typically range from 0.0 to 1.0:

0.0-0.2: Very focused and deterministic responses, ideal for code analysis and planning
0.3-0.5: Balanced responses with some creativity, good for general development tasks
0.6-1.0: More creative and varied responses, useful for brainstorming and exploration
opencode.json
{
  "agent": {
    "analyze": {
      "temperature": 0.1,
      "prompt": "{file:./prompts/analysis.txt}"
    },
    "build": {
      "temperature": 0.3
    },
    "brainstorm": {
      "temperature": 0.7,
      "prompt": "{file:./prompts/creative.txt}"
    }
  }
}

If no temperature is specified, OpenCode uses model-specific defaults; typically 0 for most models, 0.55 for Qwen models.

Max steps
Control the maximum number of agentic iterations an agent can perform before being forced to respond with text only. This allows users who wish to control costs to set a limit on agentic actions.

If this is not set, the agent will continue to iterate until the model chooses to stop or the user interrupts the session.

opencode.json
{
  "agent": {
    "quick-thinker": {
      "description": "Fast reasoning with limited iterations",
      "prompt": "You are a quick thinker. Solve problems with minimal steps.",
      "maxSteps": 5
    }
  }
}

When the limit is reached, the agent receives a special system prompt instructing it to respond with a summarization of its work and recommended remaining tasks.

Disable
Set to true to disable the agent.

opencode.json
{
  "agent": {
    "review": {
      "disable": true
    }
  }
}

Prompt
Specify a custom system prompt file for this agent with the prompt config. The prompt file should contain instructions specific to the agent’s purpose.

opencode.json
{
  "agent": {
    "review": {
      "prompt": "{file:./prompts/code-review.txt}"
    }
  }
}

This path is relative to where the config file is located. So this works for both the global OpenCode config and the project specific config.

Model
Use the model config to override the model for this agent. Useful for using different models optimized for different tasks. For example, a faster model for planning, a more capable model for implementation.

Tip

If you don’t specify a model, primary agents use the model globally configured while subagents will use the model of the primary agent that invoked the subagent.

opencode.json
{
  "agent": {
    "plan": {
      "model": "anthropic/claude-haiku-4-20250514"
    }
  }
}

The model ID in your OpenCode config uses the format provider/model-id. For example, if you’re using OpenCode Zen, you would use opencode/gpt-5.1-codex for GPT 5.1 Codex.

Tools
Control which tools are available in this agent with the tools config. You can enable or disable specific tools by setting them to true or false.

opencode.json
{
  "$schema": "https://opencode.ai/config.json",
  "tools": {
    "write": true,
    "bash": true
  },
  "agent": {
    "plan": {
      "tools": {
        "write": false,
        "bash": false
      }
    }
  }
}

Note

The agent-specific config overrides the global config.

You can also use wildcards to control multiple tools at once. For example, to disable all tools from an MCP server:

opencode.json
{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "readonly": {
      "tools": {
        "mymcp_*": false,
        "write": false,
        "edit": false
      }
    }
  }
}

Learn more about tools.

Permissions
You can configure permissions to manage what actions an agent can take. Currently, the permissions for the edit, bash, and webfetch tools can be configured to:

"ask" — Prompt for approval before running the tool
"allow" — Allow all operations without approval
"deny" — Disable the tool
opencode.json
{
  "$schema": "https://opencode.ai/config.json",
  "permission": {
    "edit": "deny"
  }
}

You can override these permissions per agent.

opencode.json
{
  "$schema": "https://opencode.ai/config.json",
  "permission": {
    "edit": "deny"
  },
  "agent": {
    "build": {
      "permission": {
        "edit": "ask"
      }
    }
  }
}

You can also set permissions in Markdown agents.

~/.config/opencode/agents/review.md
---
description: Code review without edits
mode: subagent
permission:
  edit: deny
  bash:
    "*": ask
    "git diff": allow
    "git log*": allow
    "grep *": allow
  webfetch: deny
---

Only analyze code and suggest changes.

You can set permissions for specific bash commands.

opencode.json
{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "build": {
      "permission": {
        "bash": {
          "git push": "ask",
          "grep *": "allow"
        }
      }
    }
  }
}

This can take a glob pattern.

opencode.json
{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "build": {
      "permission": {
        "bash": {
          "git *": "ask"
        }
      }
    }
  }
}

And you can also use the * wildcard to manage permissions for all commands. Since the last matching rule takes precedence, put the * wildcard first and specific rules after.

opencode.json
{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "build": {
      "permission": {
        "bash": {
          "*": "ask",
          "git status *": "allow"
        }
      }
    }
  }
}

Learn more about permissions.

Mode
Control the agent’s mode with the mode config. The mode option is used to determine how the agent can be used.

opencode.json
{
  "agent": {
    "review": {
      "mode": "subagent"
    }
  }
}

The mode option can be set to primary, subagent, or all. If no mode is specified, it defaults to all.

Hidden
Hide a subagent from the @ autocomplete menu with hidden: true. Useful for internal subagents that should only be invoked programmatically by other agents via the Task tool.

opencode.json
{
  "agent": {
    "internal-helper": {
      "mode": "subagent",
      "hidden": true
    }
  }
}

This only affects user visibility in the autocomplete menu. Hidden agents can still be invoked by the model via the Task tool if permissions allow.

Note

Only applies to mode: subagent agents.

Task permissions
Control which subagents an agent can invoke via the Task tool with permission.task. Uses glob patterns for flexible matching.

opencode.json
{
  "agent": {
    "orchestrator": {
      "mode": "primary",
      "permission": {
        "task": {
          "*": "deny",
          "orchestrator-*": "allow",
          "code-reviewer": "ask"
        }
      }
    }
  }
}

When set to deny, the subagent is removed from the Task tool description entirely, so the model won’t attempt to invoke it.

Tip

Rules are evaluated in order, and the last matching rule wins. In the example above, orchestrator-planner matches both * (deny) and orchestrator-* (allow), but since orchestrator-* comes after *, the result is allow.

Tip

Users can always invoke any subagent directly via the @ autocomplete menu, even if the agent’s task permissions would deny it.

Additional
Any other options you specify in your agent configuration will be passed through directly to the provider as model options. This allows you to use provider-specific features and parameters.

For example, with OpenAI’s reasoning models, you can control the reasoning effort:

opencode.json
{
  "agent": {
    "deep-thinker": {
      "description": "Agent that uses high reasoning effort for complex problems",
      "model": "openai/gpt-5",
      "reasoningEffort": "high",
      "textVerbosity": "low"
    }
  }
}

These additional options are model and provider-specific. Check your provider’s documentation for available parameters.

Tip

Run opencode models to see a list of the available models.

Create agents
You can create new agents using the following command:

Terminal window
opencode agent create

This interactive command will:

Ask where to save the agent; global or project-specific.
Description of what the agent should do.
Generate an appropriate system prompt and identifier.
Let you select which tools the agent can access.
Finally, create a markdown file with the agent configuration.
Use cases
Here are some common use cases for different agents.

Build agent: Full development work with all tools enabled
Plan agent: Analysis and planning without making changes
Review agent: Code review with read-only access plus documentation tools
Debug agent: Focused on investigation with bash and read tools enabled
Docs agent: Documentation writing with file operations but no system commands
Examples
Here are some example agents you might find useful.

Tip

Do you have an agent you’d like to share? Submit a PR.

Documentation agent
~/.config/opencode/agents/docs-writer.md
---
description: Writes and maintains project documentation
mode: subagent
tools:
  bash: false
---

You are a technical writer. Create clear, comprehensive documentation.

Focus on:

- Clear explanations
- Proper structure
- Code examples
- User-friendly language

Security auditor
~/.config/opencode/agents/security-auditor.md
---
description: Performs security audits and identifies vulnerabilities
mode: subagent
tools:
  write: false
  edit: false
---

You are a security expert. Focus on identifying potential security issues.

Look for:

- Input validation vulnerabilities
- Authentication and authorization flaws
- Data exposure risks
- Dependency vulnerabilities
- Configuration security issues



# Commands

Commands
Create custom commands for repetitive tasks.

Custom commands let you specify a prompt you want to run when that command is executed in the TUI.

/my-command

Custom commands are in addition to the built-in commands like /init, /undo, /redo, /share, /help. Learn more.

Create command files
Create markdown files in the commands/ directory to define custom commands.

Create .opencode/commands/test.md:

.opencode/commands/test.md
---
description: Run tests with coverage
agent: build
model: anthropic/claude-3-5-sonnet-20241022
---

Run the full test suite with coverage report and show any failures.
Focus on the failing tests and suggest fixes.

The frontmatter defines command properties. The content becomes the template.

Use the command by typing / followed by the command name.

"/test"

Configure
You can add custom commands through the OpenCode config or by creating markdown files in the commands/ directory.

JSON
Use the command option in your OpenCode config:

opencode.jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "command": {
    // This becomes the name of the command
    "test": {
      // This is the prompt that will be sent to the LLM
      "template": "Run the full test suite with coverage report and show any failures.\nFocus on the failing tests and suggest fixes.",
      // This is shown as the description in the TUI
      "description": "Run tests with coverage",
      "agent": "build",
      "model": "anthropic/claude-3-5-sonnet-20241022"
    }
  }
}

Now you can run this command in the TUI:

/test

Markdown
You can also define commands using markdown files. Place them in:

Global: ~/.config/opencode/commands/
Per-project: .opencode/commands/
~/.config/opencode/commands/test.md
---
description: Run tests with coverage
agent: build
model: anthropic/claude-3-5-sonnet-20241022
---

Run the full test suite with coverage report and show any failures.
Focus on the failing tests and suggest fixes.

The markdown file name becomes the command name. For example, test.md lets you run:

/test

Prompt config
The prompts for the custom commands support several special placeholders and syntax.

Arguments
Pass arguments to commands using the $ARGUMENTS placeholder.

.opencode/commands/component.md
---
description: Create a new component
---

Create a new React component named $ARGUMENTS with TypeScript support.
Include proper typing and basic structure.

Run the command with arguments:

/component Button

And $ARGUMENTS will be replaced with Button.

You can also access individual arguments using positional parameters:

$1 - First argument
$2 - Second argument
$3 - Third argument
And so on…
For example:

.opencode/commands/create-file.md
---
description: Create a new file with content
---

Create a file named $1 in the directory $2
with the following content: $3

Run the command:

/create-file config.json src "{ \"key\": \"value\" }"

This replaces:

$1 with config.json
$2 with src
$3 with { "key": "value" }
Shell output
To inject bash command output into your prompt, write the exclamation mark followed by the command inside backticks. The command will execute and its output will be inserted into the prompt.

Syntax description: The exclamation mark tells OpenCode to execute what follows. The backticks contain the shell command to run.

Commands run in your project's root directory and their output becomes part of the prompt.

File references
Include files in your command using @ followed by the filename.

.opencode/commands/review-component.md
---
description: Review component
---

Review the component in @src/components/Button.tsx.
Check for performance issues and suggest improvements.

The file content gets included in the prompt automatically.

Options
Let’s look at the configuration options in detail.

Template
The template option defines the prompt that will be sent to the LLM when the command is executed.

opencode.json
{
  "command": {
    "test": {
      "template": "Run the full test suite with coverage report and show any failures.\nFocus on the failing tests and suggest fixes."
    }
  }
}

This is a required config option.

Description
Use the description option to provide a brief description of what the command does.

opencode.json
{
  "command": {
    "test": {
      "description": "Run tests with coverage"
    }
  }
}

This is shown as the description in the TUI when you type in the command.

Agent
Use the agent config to optionally specify which agent should execute this command. If this is a subagent the command will trigger a subagent invocation by default. To disable this behavior, set subtask to false.

opencode.json
{
  "command": {
    "review": {
      "agent": "plan"
    }
  }
}

This is an optional config option. If not specified, defaults to your current agent.

Subtask
Use the subtask boolean to force the command to trigger a subagent invocation. This is useful if you want the command to not pollute your primary context and will force the agent to act as a subagent, even if mode is set to primary on the agent configuration.

opencode.json
{
  "command": {
    "analyze": {
      "subtask": true
    }
  }
}

This is an optional config option.

Model
Use the model config to override the default model for this command.

opencode.json
{
  "command": {
    "analyze": {
      "model": "anthropic/claude-3-5-sonnet-20241022"
    }
  }
}

This is an optional config option.

Built-in
opencode includes several built-in commands like /init, /undo, /redo, /share, /help; learn more.

Note

Custom commands can override built-in commands.

If you define a custom command with the same name, it will override the built-in command.

Edit this page

# Skills

Agent Skills
Define reusable behavior via SKILL.md definitions

Agent skills let OpenCode discover reusable instructions from your repo or home directory. Skills are loaded on-demand via the native skill tool—agents see available skills and can load the full content when needed.

Place files
Create one folder per skill name and put a SKILL.md inside it. OpenCode searches these locations:

Project config: .opencode/skills/<name>/SKILL.md
Global config: ~/.config/opencode/skills/<name>/SKILL.md
Project Claude-compatible: .claude/skills/<name>/SKILL.md
Global Claude-compatible: ~/.claude/skills/<name>/SKILL.md
Understand discovery
For project-local paths, OpenCode walks up from your current working directory until it reaches the git worktree. It loads any matching skills/*/SKILL.md in .opencode/ and any matching .claude/skills/*/SKILL.md along the way.

Global definitions are also loaded from ~/.config/opencode/skills/*/SKILL.md and ~/.claude/skills/*/SKILL.md.

Write frontmatter
Each SKILL.md must start with YAML frontmatter. Only these fields are recognized:

name (required)
description (required)
license (optional)
compatibility (optional)
metadata (optional, string-to-string map)
Unknown frontmatter fields are ignored.

Validate names
name must:

Be 1–64 characters
Be lowercase alphanumeric with single hyphen separators
Not start or end with -
Not contain consecutive --
Match the directory name that contains SKILL.md
Equivalent regex:

^[a-z0-9]+(-[a-z0-9]+)*$

Follow length rules
description must be 1-1024 characters. Keep it specific enough for the agent to choose correctly.

Use an example
Create .opencode/skills/git-release/SKILL.md like this:

---
name: git-release
description: Create consistent releases and changelogs
license: MIT
compatibility: opencode
metadata:
  audience: maintainers
  workflow: github
---

## What I do

- Draft release notes from merged PRs
- Propose a version bump
- Provide a copy-pasteable `gh release create` command

## When to use me

Use this when you are preparing a tagged release.
Ask clarifying questions if the target versioning scheme is unclear.

Recognize tool description
OpenCode lists available skills in the skill tool description. Each entry includes the skill name and description:

<available_skills>
  <skill>
    <name>git-release</name>
    <description>Create consistent releases and changelogs</description>
  </skill>
</available_skills>

The agent loads a skill by calling the tool:

skill({ name: "git-release" })

Configure permissions
Control which skills agents can access using pattern-based permissions in opencode.json:

{
  "permission": {
    "skill": {
      "*": "allow",
      "pr-review": "allow",
      "internal-*": "deny",
      "experimental-*": "ask"
    }
  }
}

Permission	Behavior
allow	Skill loads immediately
deny	Skill hidden from agent, access rejected
ask	User prompted for approval before loading
Patterns support wildcards: internal-* matches internal-docs, internal-tools, etc.

Override per agent
Give specific agents different permissions than the global defaults.

For custom agents (in agent frontmatter):

---
permission:
  skill:
    "documents-*": "allow"
---

For built-in agents (in opencode.json):

{
  "agent": {
    "plan": {
      "permission": {
        "skill": {
          "internal-*": "allow"
        }
      }
    }
  }
}

Disable the skill tool
Completely disable skills for agents that shouldn’t use them:

For custom agents:

---
tools:
  skill: false
---

For built-in agents:

{
  "agent": {
    "plan": {
      "tools": {
        "skill": false
      }
    }
  }
}

When disabled, the <available_skills> section is omitted entirely.

Troubleshoot loading
If a skill does not show up:

Verify SKILL.md is spelled in all caps
Check that frontmatter includes name and description
Ensure skill names are unique across all locations
Check permissions—skills with deny are hidden from agents

# Tools

Custom Tools
Create tools the LLM can call in opencode.

Custom tools are functions you create that the LLM can call during conversations. They work alongside opencode’s built-in tools like read, write, and bash.

Creating a tool
Tools are defined as TypeScript or JavaScript files. However, the tool definition can invoke scripts written in any language — TypeScript or JavaScript is only used for the tool definition itself.

Location
They can be defined:

Locally by placing them in the .opencode/tools/ directory of your project.
Or globally, by placing them in ~/.config/opencode/tools/.
Structure
The easiest way to create tools is using the tool() helper which provides type-safety and validation.

.opencode/tools/database.ts
import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "Query the project database",
  args: {
    query: tool.schema.string().describe("SQL query to execute"),
  },
  async execute(args) {
    // Your database logic here
    return `Executed query: ${args.query}`
  },
})

The filename becomes the tool name. The above creates a database tool.

Multiple tools per file
You can also export multiple tools from a single file. Each export becomes a separate tool with the name <filename>_<exportname>:

.opencode/tools/math.ts
import { tool } from "@opencode-ai/plugin"

export const add = tool({
  description: "Add two numbers",
  args: {
    a: tool.schema.number().describe("First number"),
    b: tool.schema.number().describe("Second number"),
  },
  async execute(args) {
    return args.a + args.b
  },
})

export const multiply = tool({
  description: "Multiply two numbers",
  args: {
    a: tool.schema.number().describe("First number"),
    b: tool.schema.number().describe("Second number"),
  },
  async execute(args) {
    return args.a * args.b
  },
})

This creates two tools: math_add and math_multiply.

Arguments
You can use tool.schema, which is just Zod, to define argument types.

args: {
  query: tool.schema.string().describe("SQL query to execute")
}

You can also import Zod directly and return a plain object:

import { z } from "zod"

export default {
  description: "Tool description",
  args: {
    param: z.string().describe("Parameter description"),
  },
  async execute(args, context) {
    // Tool implementation
    return "result"
  },
}

Context
Tools receive context about the current session:

.opencode/tools/project.ts
import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "Get project information",
  args: {},
  async execute(args, context) {
    // Access context information
    const { agent, sessionID, messageID } = context
    return `Agent: ${agent}, Session: ${sessionID}, Message: ${messageID}`
  },
})

Examples
Write a tool in Python
You can write your tools in any language you want. Here’s an example that adds two numbers using Python.

First, create the tool as a Python script:

.opencode/tools/add.py
import sys

a = int(sys.argv[1])
b = int(sys.argv[2])
print(a + b)

Then create the tool definition that invokes it:

.opencode/tools/python-add.ts
import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "Add two numbers using Python",
  args: {
    a: tool.schema.number().describe("First number"),
    b: tool.schema.number().describe("Second number"),
  },
  async execute(args) {
    const result = await Bun.$`python3 .opencode/tools/add.py ${args.a} ${args.b}`.text()
    return result.trim()
  },
})

Here we are using the Bun.$ utility to run the Python script.