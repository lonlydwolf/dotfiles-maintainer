# Jujutsu (jj) CLI Reference

This project primarily uses [Jujutsu (jj)](https://github.com/martinvonz/jj) for version control. While `jj` is backed by Git and fully interoperable, we recommend using `jj` commands for the best development experience.

## Core Concepts

*   **Change:** Every commit is a "change". You are always working on a change.
*   **Working Copy (`@`):** The current state of your files is effectively a mutable commit.
*   **Bookmark:** Equivalent to a Git branch. A pointer to a specific change.
*   **Colocated:** This repository is configured so `jj` and `git` share the same `.git` folder.

## Cheatsheet

### Basics

| Goal | Command | Git Equivalent |
| :--- | :--- | :--- |
| **Check status** | `jj st` | `git status` |
| **Show log** | `jj log` | `git log --graph` |
| **Start new work** | `jj new main` | `git checkout -b feature` |
| **Save work** | `jj describe -m "msg"` | `git commit -m "msg"` |
| **Edit history** | `jj squash` | `git rebase -i` (squash) |
| **Undo** | `jj undo` | *No direct equivalent* |

### Workflow

1.  **Start work:**
    ```bash
    jj new main
    ```
    *Creates an anonymous empty change on top of main.*

2.  **Make changes:**
    Edit files. `jj st` will show them as modified in the working copy.

3.  **Snapshot & Describe:**
    ```bash
    jj describe -m "feat(scope): add new feature"
    ```
    *Updates the description of the current change.*

4.  **Create a Branch (Bookmark):**
    ```bash
    jj bookmark create feat/my-feature
    ```
    *Assigns a name to the current change.*

5.  **Push:**
    ```bash
    jj git push
    ```
    *Pushes the bookmark to the remote.*

### Advanced

*   **Split a change:** `jj split` (Interactive UI to separate changes)
*   **Move changes:** `jj rebase -d main` (Rebase current change onto main)
*   **Resolve conflicts:** `jj resolve` (or standard merge tool)

## Git Interoperability

You can use standard Git commands (`git status`, `git pull`, etc.) alongside `jj`.
*   `jj` automatically detects changes made by `git`.
*   `jj git import`: Manually import git refs if they get out of sync.
*   `jj git export`: Manually export `jj` changes to git refs (usually automatic).
