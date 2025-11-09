# src/git_logging.py
import os, json, time, subprocess, difflib
from datetime import datetime
from pathlib import Path


class GitLogger:
    """
    Minimalistische Git-Integration per subprocess (keine Fremdabhängigkeiten).
    Schreibt Artefakte unter .adaptation/<run_id>/..., commit-t alles whitelisted.
    """

    def __init__(
        self,
        repo_dir: str,
        run_id: str,
        branch_prefix: str = "adapt",
        author_name: str | None = None,
        author_email: str | None = None,
    ):
        self.repo = os.path.abspath(repo_dir)
        self.run_id = run_id
        self.branch = f"{branch_prefix}/{run_id}"
        self.adapt_dir = os.path.join(self.repo, ".adaptation", run_id)
        os.makedirs(self.adapt_dir, exist_ok=True)
        self._ensure_repo()
        self._config_user(author_name, author_email)

    # ---- low-level helpers ---------------------------------------------------
    def _git(self, *args, check=True, input=None):
        return subprocess.run(
            ["git", "-C", self.repo, *args],
            text=True,
            capture_output=True,
            check=check,
            input=input,
        )

    def _ensure_repo(self):
        r = subprocess.run(
            ["git", "-C", self.repo, "rev-parse", "--is-inside-work-tree"],
            text=True,
            capture_output=True,
        )
        if r.returncode != 0:
            self._git("init")

    def _config_user(self, name, email):
        self._git(
            "config", "user.name", name or os.getenv("GIT_AUTHOR_NAME", "AdaptationBot")
        )
        self._git(
            "config",
            "user.email",
            email or os.getenv("GIT_AUTHOR_EMAIL", "adaptation@example.com"),
        )

    # ---- lifecycle -----------------------------------------------------------
    def start_run_branch(self, base_ref: str | None = None) -> str:
        base = base_ref or "HEAD"
        # create or reset branch to base
        exists = (
            subprocess.run(
                [
                    "git",
                    "-C",
                    self.repo,
                    "show-ref",
                    "--verify",
                    f"refs/heads/{self.branch}",
                ],
                capture_output=True,
            ).returncode
            == 0
        )
        if exists:
            self._git("checkout", self.branch)
        else:
            self._git("checkout", "-B", self.branch, base)
        return self.branch

    # ---- artifacts -----------------------------------------------------------
    def write_artifact(self, rel_path: str, content: str, binary: bool = False) -> str:
        path = os.path.join(self.adapt_dir, rel_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        mode = "wb" if binary else "w"
        with open(path, mode, encoding=None if binary else "utf-8") as f:
            f.write(content if binary else str(content))
        return os.path.relpath(path, self.repo)

    def write_diff(self, before_text: str, after_text: str, dest_rel_dir: str) -> str:
        patch = difflib.unified_diff(
            before_text.splitlines(True),
            after_text.splitlines(True),
            fromfile="before.java",
            tofile="after.java",
            n=3,
        )
        return self.write_artifact(f"{dest_rel_dir}/test.diff", "".join(patch))

    # ---- committing ----------------------------------------------------------
    def commit_checkpoint(
        self,
        step: str,
        *,
        attempt: int | None = None,
        outcome: str | None = None,
        add_paths: list[str] | None = None,
        trailers: dict[str, str] | None = None,
        metadata: dict | None = None,
        tag: str | None = None,
    ) -> str:
        meta = {
            **(metadata or {}),
            "run_id": self.run_id,
            "step": step,
            "attempt": attempt,
            "outcome": outcome,
            "ts_unix": int(time.time()),
            "ts_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }
        meta_rel = self.write_artifact(f"{step}/meta.json", json.dumps(meta, indent=2))

        to_add = [meta_rel]
        for p in add_paths or []:
            if not p:
                continue
            abs_p = (
                os.path.abspath(os.path.join(self.repo, p))
                if not os.path.isabs(p)
                else p
            )
            # nur Dateien innerhalb des Repo-Wurzelverzeichnisses
            if os.path.commonpath([abs_p, self.repo]) != self.repo:
                continue
            to_add.append(os.path.relpath(abs_p, self.repo))

        if to_add:
            self._git("add", "--", *to_add)

        # Commit-Message mit Commit-Trailern (später gut parsbar)
        lines = [
            f"adapt: {step}" + (f" (attempt {attempt})" if attempt else ""),
            "",
            "Artifacts:",
            f"  - {meta_rel}",
        ]
        if trailers:
            lines.append("")
            for k, v in trailers.items():
                lines.append(f"{k}: {v}")
        msg = "\n".join(lines) + "\n"

        self._git("commit", "-m", msg)
        sha = self._git("rev-parse", "HEAD").stdout.strip()
        if tag:
            self._git("tag", "-f", tag)
        return sha

    def tag_attempt(self, attempt: int, status: str) -> str:
        name = f"{self.run_id}/attempt-{attempt}-{status}"
        self._git("tag", "-f", name)
        return name

    def add_note_json(self, obj: dict, ref: str = "HEAD"):
        payload = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        self._git("notes", "add", "-f", "-m", payload, ref)
