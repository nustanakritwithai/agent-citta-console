# Security

The console can dispatch actions back into a runtime, so the permission layer is
part of the core design.

## Safe actions

Safe actions inspect or summarize:

- `view_trace`
- `view_diff`
- `summarize_state`
- `inspect_error`
- `read_file`
- `show_logs`

## Medium actions

Medium actions should ask for confirmation in the UI:

- `run_tests`
- `create_file`
- `edit_draft`
- `redirect_task`
- `pause_agent`

## Dangerous actions

Dangerous actions require explicit confirmation:

- `delete_file`
- `overwrite_file`
- `run_shell_command`
- `install_package`
- `git_push`
- `deploy`
- `modify_many_files`

The local console records these as `pending_confirmation` first. `POST /confirm`
appends a `confirmed` audit record, and `POST /cancel` appends a `blocked` audit
record. The core dispatcher still does not execute the action.

## Forbidden by default

These actions are blocked unless a deployment explicitly opts into them:

- `delete_project`
- `send_email`
- `publish_content`
- `deploy_production`
- `wipe_memory`

Rules:

1. Every action must include a reason.
2. Every action must be logged.
3. Dangerous actions require confirmation.
4. File-changing actions should expose a diff.
5. Destructive actions should have a rollback plan.
6. The v0.2 core does not implement shell execution, deploy, git push, or delete
   execution.
