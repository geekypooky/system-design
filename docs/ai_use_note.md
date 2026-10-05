# AI Use Note

The AI (Antigravity) was used to generate the foundation, Docker orchestration, initial Python backend files, the dashboard, Locust testing file, and SQL schemas.

Tools used:
- `write_to_file` to write all files
- `invoke_subagent` to delegate Python backend logic to a fast subagent
- `run_command` to setup the file hierarchy.

Generated: 
Docker layout, Nginx load balancing, Locust test script, UI dashboard, and Postgres schema. Python backend and workers created via subagents.

Validated via `locust` scenarios and invariant checking.
