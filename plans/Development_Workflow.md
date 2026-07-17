# Development Workflow

> Day-to-day implementation guide for the DuckyScript 3 interpreter  
> Used alongside: DuckyScript3_Engineering_Spec.md (Frozen) · DuckyScript3_Implementation_Roadmap.md  

---

## Milestone Workflow

For **every** milestone, in order:

### 1. Explain the goal before writing code
State which milestone you are starting and what it achieves. Confirm the approach before typing any code.

### 2. List every file that will be created or modified
Write down the exact file paths before touching them. This prevents scope creep and accidental edits.

### 3. Implement only the current milestone
Do not add code for future milestones. Do not add speculative abstractions "for later." If something needed for a future milestone is missing, complete the current milestone first and report the gap.

### 4. Complete every acceptance criterion from the roadmap
The roadmap lists acceptance criteria per milestone. All must pass. No partial completions.

### 5. Run all tests before considering the milestone complete
`pytest tests/` — all tests must pass. A milestone is not done if any test fails.

### 6. Report any assumptions made
If implementation required a decision not covered by the spec or roadmap, document it. Example: "Assumed `$` sigil must immediately precede the identifier without whitespace."

### 7. Report any technical debt introduced
If a shortcut was taken (e.g., O(n²) scan where O(1) is possible), document it with a `# ponytail:` comment in code and note it in the completion report.

### 8. Stop and wait for approval before beginning the next milestone
Do not chain milestones. After committing M1, stop and wait for explicit approval to start M2.

---

## Specification Rules

- **The Engineering Specification is frozen.** Do not modify it unless explicitly instructed.
- The roadmap may be updated only if implementation requires it **and** the change is approved.
- If implementation reveals an ambiguity or conflict in the spec, stop immediately and report it. Do not guess.
- Never silently change the architecture, language behavior, or interface contracts.

---

## Git Workflow

Every completed milestone produces exactly **one** Git commit.

### Pre-commit checklist

1. Review all acceptance criteria for the milestone — all checked off.
2. Run `pytest tests/` — all tests pass.
3. Review every modified file with `git diff`.
4. Run `ruff check src/ tests/` and `mypy src/ tests/` — both clean.
5. Stage **only** the files belonging to this milestone.
6. Create exactly one commit.

### Commit message format

```
Milestone X: <short description>
```

Examples:

```
Milestone 1: Repository scaffold
Milestone 2: Token definitions
Milestone 3: Lexer implementation
Milestone 4: AST definitions
Milestone 5: Parser implementation
```

Do not combine multiple milestones into a single commit. Do not commit unfinished work.

### After commit

Push only when the milestone is complete and reviewed.

---

## Basic Git Commands

| Command | Purpose |
|---------|---------|
| `git status` | Show which files are modified, staged, or untracked. Run this before every commit. |
| `git add .` | Stage all changed files in the repository. Use with caution — prefer `git add <file>`. |
| `git add <file>` | Stage specific file(s) for commit. Always prefer this over `git add .` to avoid accidently including unrelated files. |
| `git commit -m "Milestone X: ..."` | Create a commit with the specified message. Follow the required format. |
| `git push` | Push local commits to the remote repository. |
| `git log --oneline` | Show the commit history as a compact one-line-per-commit listing. |
| `git diff` | Show unstaged changes (working tree vs staging area). Use before `git add` to review what changed. |
| `git restore <file>` | Discard unstaged changes to a file, reverting it to the last committed version. |
| `git restore --staged <file>` | Unstage a file without discarding local changes (keeps edits in working tree). |
| `git branch` | List local branches. The current branch is marked with `*`. |
| `git checkout <branch>` | Switch to an existing branch. Use `git checkout -b <name>` to create and switch to a new branch. |

---

## Implementation Principles

1. **One milestone at a time.** Never jump ahead. Never combine milestones.
2. **Never write untestable code.** Every function and class must be reachable from a test. No dead code.
3. **No placeholder implementations.** Every method must have a real implementation. If a method genuinely cannot be implemented yet, it must explicitly raise `NotImplementedError` with a clear message — and this must be approved.
4. **No TODO comments.** If something is deferred, it must either be a tracked issue or not exist. TODO comments rot.
5. **Small, focused commits.** If a milestone feels too large to commit as one piece, it should be broken into sub-milestones (and the roadmap updated).
6. **Always buildable, always testable.** After every change, the project must install and tests must (at minimum) run without crashing, even if some tests are not yet written.
7. **Prioritize correctness over speed.** Correct first. Clear second. Fast third. Never sacrifice correctness for performance.
8. **When in doubt, ask.** If any rule above conflicts with the situation, stop and ask before proceeding.
9. **Mark deliberate shortcuts.** If ponytail mode (lazy implementation) is used, mark with `# ponytail: <reason>` comments and note the ceiling and upgrade path.
