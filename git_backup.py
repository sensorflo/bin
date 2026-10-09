R"""Back up unpushed git work of all git repos below SEARCH_ROOTS into OneDrive.

For each repo, one bundle file holds everything not yet on any remote: unpushed
commits of all branches, all stashes, and the current uncommitted changes.

Restore after losing the laptop:
    git clone <remote> <dir>
    cd <dir>
    git bundle verify <bundle>
    git fetch <bundle> "refs/*:refs/restored/*"
"""
# For usage, run with --help

import argparse
import os
import subprocess
import sys
from pathlib import Path

SEARCH_ROOTS = [Path.home() / "src"]
SKIP_DIR_NAMES = {"node_modules"}
BUNDLE_DIR_NAME = "git-backup"
TEMP_REF_PREFIX = "refs/backup/"


def bundle_dir():
    onedrive = os.environ.get("OneDriveCommercial") or os.environ.get("OneDrive")
    if not onedrive:
        sys.exit("Neither %OneDriveCommercial% nor %OneDrive% is set: is OneDrive set up?")
    return Path(onedrive, BUNDLE_DIR_NAME)


def find_repos(root):
    for dirpath, dirnames, filenames in os.walk(root):
        if ".git" in dirnames or ".git" in filenames:
            yield Path(dirpath)
            dirnames.clear()
        else:
            dirnames[:] = [name for name in dirnames if name not in SKIP_DIR_NAMES]


def git(repo, *args, check=True):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=check,
                          env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})


def backup_repo(repo, bundle):
    """Write repo's unpushed work to bundle. Return a short status text."""
    fetch = git(repo, "fetch", "--all", "--prune", "--quiet", check=False)
    warning = "" if fetch.returncode == 0 else " (fetch failed, remote state may be stale)"

    temp_refs = []
    try:
        for i, sha in enumerate(git(repo, "stash", "list", "--format=%H").stdout.split()):
            temp_refs.append(f"{TEMP_REF_PREFIX}stash-{i}")
            git(repo, "update-ref", temp_refs[-1], sha)
        uncommitted = git(repo, "stash", "create").stdout.strip()
        if uncommitted:
            temp_refs.append(f"{TEMP_REF_PREFIX}uncommitted")
            git(repo, "update-ref", temp_refs[-1], uncommitted)

        temp_bundle = bundle.with_name(bundle.name + ".tmp")
        result = git(repo, "bundle", "create", str(temp_bundle), "--all", "--not", "--remotes", check=False)
    finally:
        for ref in temp_refs:
            git(repo, "update-ref", "-d", ref)

    if result.returncode != 0:
        if "empty bundle" in result.stderr:
            bundle.unlink(missing_ok=True)
            return "nothing unpushed" + warning
        raise RuntimeError(result.stderr.strip())
    os.replace(temp_bundle, bundle)
    return f"{bundle.stat().st_size / 1024:,.0f} KB" + warning


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--list", action="store_true", help="only list the git repos found")
    args = parser.parse_args()

    repos = [(root, repo) for root in SEARCH_ROOTS for repo in find_repos(root)]
    if args.list:
        for _, repo in repos:
            print(repo)
        return

    target_dir = bundle_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    failed = 0
    for root, repo in repos:
        bundle = target_dir / ("__".join((root.name, *repo.relative_to(root).parts)) + ".bundle")
        try:
            print(f"{repo}: {backup_repo(repo, bundle)}")
        except (RuntimeError, subprocess.CalledProcessError) as error:
            failed += 1
            print(f"{repo}: FAILED: {getattr(error, 'stderr', None) or error}", file=sys.stderr)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
