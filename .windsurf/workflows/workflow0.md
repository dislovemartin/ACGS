---
description: Command Reference
---

 **Command Reference: parse-prd**
  - Legacy Syntax: `node scripts/dev.js parse-prd --input=<prd-file.txt>`
  - CLI Syntax: `task-master parse-prd --input=<prd-file.txt>`
  - Description: Parses a PRD document and generates a tasks.json file with structured tasks
  - Parameters: 
    - `--input=<file>`: Path to the PRD text file (default: sample-prd.txt)
  - Example: `task-master parse-prd --input=requirements.txt`
  - Notes: Will overwrite existing tasks.json file. Use with caution.

- **Command Reference: update**
  - Legacy Syntax: `node scripts/dev.js update --from=<id> --prompt="<prompt>"`
  - CLI Syntax: `task-master update --from=<id> --prompt="<prompt>"`
  - Description: Updates tasks with ID >= specified ID based on the provided prompt
  - Parameters:
    - `--from=<id>`: Task ID from which to start updating (required)
    - `--prompt="<text>"`: Explanation of changes or new context (required)
  - Example: `task-master update --from=4 --prompt="Now we are using Express instead of Fastify."`
  - Notes: Only updates tasks not marked as 'done'. Completed tasks remain unchanged.

- **Command Reference: generate**
  - Legacy Syntax: `node scripts/dev.js generate`
  - CLI Syntax: `task-master generate`
  - Description: Generates individual task files in tasks/ directory based on tasks.json
  - Parameters: 
    - `--file=<path>, -f`: Use alternative tasks.json file (default: 'tasks/tasks.json')
    - `--output=<dir>, -o`: Output directory (default: 'tasks')
  - Example: `task-master generate`
  - Notes: Overwrites existing task files. Creates tasks/ directory if needed.

- **Command Reference: set-status**
  - Legacy Syntax: `node scripts/dev.js set-status --id=<id> --status=<status>`
  - CLI Syntax: `task-master set-status --id=<id> --status=<status>`
  - Description: Updates the status of a specific task in tasks.json
  - Parameters:
    - `--id=<id>`: ID of the task to update (required)
    - `--status=<status>`: New status value (required)
  - Example: `task-master set-status --id=3 --status=done`
  - Notes: Common values are 'done', 'pending', and 'deferred', but any string is accepted.

- **Command Reference: list**
  - Legacy Syntax: `node scripts/dev.js list`
  - CLI Syntax: `task-master list`
  - Description: Lists all tasks in tasks.json with IDs, titles, and status
  - Parameters: 
    - `--status=<status>, -s`: Filter by status
    - `--with-subtasks`: Show subtasks for each task
    - `--file=<path>, -f`: Use alternative tasks.json file (default: 'tasks/tasks.json')
  - Example: `task-master list`
  - Notes: Provides quick overview of project progress. Use at start of sessions.

- **Command Reference: expand**
  - Legacy Syntax: `node scripts/dev.js expand --id=<id> [--num=<number>] [--research] [--prompt="<context>"]`
  - CLI Syntax: `task-master expand --id=<id> [--num=<number>] [--research] [--prompt="<context>"]`
  - Description: Expands a task with subtasks for detailed implementation
  - Parameters:
    - `--id=<id>`: ID of task to expand (required unless using --all)
    - `--all`: Expand all pending tasks, prioritized by complexity
    - `--num=<number>`: Number of subtasks to generate (default: from complexity report)
    - `--research`: Use Perplexity AI for research-backed generation
    - `--prompt="<text>"`: Additional context for subtask generation
    - `--force`: Regenerate subtasks even for tasks that already have them
  - Example: `task-master expand --id=3 --num=5 --research --prompt="Focus on security aspects"`
  - Notes: Uses complexity report recommendations if available.

- **Command Reference: analyze-complexity**
  - Legacy Syntax: `node scripts/dev.js analyze-complexity [options]`
  - CLI Syntax: `task-master analyze-complexity [options]`
  - Description: Analyzes task complexity and generates expansion recommendations
  - Parameters:
    - `--output=<file>, -o`: Output file path (default: scripts/task-complexity-report.json)
    - `--model=<model>, -m`: Override LLM model to use
    - `--threshold=<number>, -t`: Minimum score for expansion recommendation (default: 5)
    - `--file=<path>, -f`: Use alternative tasks.json file
    - `--research, -r`: Use Perplexity AI for research-backed analysis
  - Example: `task-master analyze-complexity --research`
  - Notes: Report includes complexity scores, recommended subtasks, and tailored prompts.

- **Command Reference: clear-subtasks**
  - Legacy Syntax: `node scripts/dev.js clear-subtasks --id=<id>`
  - CLI Syntax: `task-master clear-subtasks --id=<id>`
  - Description: Removes subtasks from specified tasks to allow regeneration
  - Parameters:
    - `--id=<id>`: ID or comma-separated IDs of tasks to clear subtasks from
    - `--all`: Clear subtasks from all tasks
  - Examples:
    - `task-master clear-subtasks --id=3`
    - `task-master clear-subtasks --id=1,2,3`
    - `task-master clear-subtasks --all`
  - Notes: 
    - Task files are automatically regenerated after clearing subtasks
    - Can be combined with expand command to immediately generate new subtasks
    - Works with both parent tasks and individual subtasks

-