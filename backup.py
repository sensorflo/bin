R"""Back up my home folder and SD card with restic, and push my unpushed version-controlled work.

Ensure Defender is turned off, or at least that restic.exe and the backup folder
are excluded from scanning.
"""
# For usage, run with --help

import argparse
import enum
import functools
import json
import os
import platform
import stat
import string
import subprocess
import sys
from pathlib import Path

# The SD card is semantically an extension of my home folder, so both go into
# one snapshot.
SD_MARKER_PATH = R"S:\.backup-source-sd"
SOURCE_PATHS = [
    R"C:\Users\Senso",
    "S:\\",
]
# Git repos below these folders get their branches, stashes and uncommitted changes pushed
# to backup/<computer name>/... branches on their remote, if the remote is mine.
GIT_SEARCH_ROOTS = [R"C:\Users\Senso\src", R"C:\Users\Senso\bin", R"C:\Users\Senso\Documents"]
# Additional single git repos, whose subfolders are not searched for further git repos.
GIT_REPOS = [R"C:\Users\Senso"]
OWN_REMOTE_PREFIXES = (
    "https://github.com/sensorflo/", "git@github.com:sensorflo/",
    "https://gitlab.com/sensorflo1/", "git@gitlab.com:sensorflo1/",
)
# Names of git repo folders that are skipped: either their remote isn't mine, or they have
# intentionally no remote. Any other git repo without a remote of mine is an error.
GIT_REPOS_WITHOUT_OWN_REMOTE = {
    "cppfront", "googletest", "vcpkg", "SyncArwDng", "console-application-gtest",
}

# The primary repo. Unqualified 'repo' and 'backup' in this script always mean the primary one.
# Each repo lives on whichever drive has its marker file in its root.
REPO_MARKER_NAME = ".backup-destination"
REPO_DIR = R"Backup\restic-backup-dell-xps-15-home-folder"
# The secondary repo holds copies of the primary repo's snapshots (restic copy).
SECONDARY_REPO_MARKER_NAME = ".secondary-backup-destination"
SECONDARY_REPO_DIR = R"Backup\secondary-restic-backup-dell-xps-15-home-folder"

# Case-insensitive restic exclude patterns (--iexclude).
EXCLUDES = [
    # _new_ .arw files are backed up separately
    R"C:\Users\Senso\Large\Pictures\Pictures\new\**\*.arw",
    R"C:\Users\Senso\Large\Pictures\Pictures\new-old\**\*.arw",
    R"S:\new\**\*.arw",
    R"S:\new-old\**\*.arw",

    # Note that non-raw image files are backed up, even the ones in the 'new'
    # 'new-old' trees. I don't have too many of those.

    # Misc
    R"**\thumbnails-digikam.db",
    R"**\*.acr", # lightroom artifacts
    R"**\.git\**", # TODO: backup unpushed commits. At least we have working tree.
    R"C:\Users\Senso\src\**\build*\**", # TODO: Maybe a tad dangerous in maybe wrongly excluding too much.
    R"C:\Users\Senso\NTUSER.DAT*",
    R"**\.dtrash\**", # darktable trash

    # Complete folders
    R"C:\Users\Senso\Large\Pictures\Temp\**",
    R"C:\Users\Senso\Large\Pictures\Lightroom\Lightroom Catalog Previews.lrdata\**",
    R"C:\Users\Senso\Large\Pictures\Lightroom\Lightroom Catalog Smart Previews.lrdata\**",
    R"C:\Users\Senso\AppData\**",
    R"C:\Users\Senso\CrossDevice\**",
    R"C:\Users\Senso\OneDrive\**",
    R"C:\Users\Senso\Downloads\**",
    R"C:\Users\Senso\src\vcpkg\**",
    R"C:\Users\Senso\src\external\**",
    R"C:\Users\Senso\.vscode\extensions\**",
    R"S:\rejected\**",
    R"S:\$RECYCLE.BIN\**",
]

@functools.cache
def find_repo_path(marker_name, repo_dir, exit_on_error=True):
    drive_letters = [drive_letter for drive_letter in string.ascii_uppercase
                     if os.path.exists(f"{drive_letter}:\\{marker_name}")]
    if len(drive_letters) == 1:
        return drive_letters[0] + ":\\" + repo_dir
    if exit_on_error:
        sys.exit(f"Expected exactly one drive with a {marker_name} file in its root, "
                 f"found: {', '.join(drive_letters) or 'none'}")
    return None


def repo_path(exit_on_error=True):
    return find_repo_path(REPO_MARKER_NAME, REPO_DIR, exit_on_error)


def secondary_repo_path(exit_on_error=True):
    return find_repo_path(SECONDARY_REPO_MARKER_NAME, SECONDARY_REPO_DIR, exit_on_error)


def path_for_help(marker_name, repo_dir):
    return find_repo_path(marker_name, repo_dir, exit_on_error=False) or f"<drive with {marker_name}>:\\{repo_dir}"


def restic(*args, repo=None):
    """Run restic with the given arguments on repo (default: the primary repo), return its exit code."""
    return subprocess.run(["restic", *args, "--repo", repo or repo_path(), "--insecure-no-password"]).returncode


def require_repo(path, init_option):
    if not (Path(path) / "config").exists():
        sys.exit(f"No restic repository at {path}. To create a new one: python backup.py {init_option}")


def chunker_polynomial(repo):
    config = subprocess.run(["restic", "cat", "config", "--repo", repo, "--insecure-no-password"],
                            capture_output=True, text=True, check=True).stdout
    return json.loads(config)["chunker_polynomial"]


def copy_script_to_drive_of(repo):
    source = Path(__file__).resolve()
    target = Path(Path(repo).anchor, source.name)
    if target.exists():
        target.chmod(stat.S_IWRITE)
    target.write_text(f"# This is a copy of {source}\n" + source.read_text(encoding="utf-8"), encoding="utf-8")
    target.chmod(stat.S_IREAD)


def restic_init():
    if Path(repo_path()).exists():
        sys.exit(f"Not initializing: {repo_path()} already exists.")
    copy_script_to_drive_of(repo_path())
    print(f"Initializing new restic repository at {repo_path()}")
    return restic("init", "--compression", "off")


def restic_backup():
    require_repo(repo_path(), "--init")
    if not Path(SD_MARKER_PATH).exists():
        sys.exit(f"SD card not found: {SD_MARKER_PATH} is missing (card not inserted, or a different "
                 "drive letter?). Not backing up, since the snapshot would be incomplete.")
    copy_script_to_drive_of(repo_path())
    print(f"Starting backup of {', '.join(SOURCE_PATHS)} ...")
    excludes = [f"--iexclude={pattern}" for pattern in EXCLUDES]
    return restic("backup", *SOURCE_PATHS, *excludes, "--compression", "off", "--verbose")


def find_git_repos(root):
    for dirpath, dirnames, filenames in os.walk(root):
        if ".git" in dirnames or ".git" in filenames:
            yield Path(dirpath)
        if ".git" in dirnames:
            dirnames.remove(".git")


def git(git_repo, *args):
    return subprocess.run(["git", "-C", str(git_repo), *args], capture_output=True, text=True, check=True,
                          env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}).stdout


def own_remote(git_repo):
    for remote in git(git_repo, "remote").split():
        if git(git_repo, "remote", "get-url", remote).strip().startswith(OWN_REMOTE_PREFIXES):
            return remote
    return None


def backup_git_repo(git_repo, remote):
    prefix = f"refs/heads/backup/{platform.node()}/"
    branches = dict(line.split() for line in
                    git(git_repo, "for-each-ref", "--format=%(refname:lstrip=2) %(objectname)", "refs/heads").splitlines())
    if any(name == "stash" or name.startswith("stash/") for name in branches):
        raise RuntimeError("a branch named 'stash' would clash with the backup of the stashes")
    wanted = {prefix + name: sha for name, sha in branches.items()}
    for i, sha in enumerate(git(git_repo, "stash", "list", "--format=%H").split()):
        wanted[f"{prefix}stash/{i}"] = sha
    uncommitted = git(git_repo, "stash", "create").strip()
    if uncommitted:
        wanted[f"{prefix}stash/uncommitted"] = uncommitted

    existing = {ref: sha for sha, ref in (line.split() for line in git(git_repo, "ls-remote", "--heads", remote).splitlines())
                if ref.startswith(prefix)}
    refspecs = [f"+{sha}:{ref}" for ref, sha in wanted.items() if existing.get(ref) != sha]
    refspecs += [f":{ref}" for ref in existing if ref not in wanted]
    if not refspecs:
        return "up to date"
    # git(git_repo, "push", "--quiet", remote, *refspecs)
    print(git(git_repo, "push", "--dry-run", "--porcelain", remote, *refspecs))
    return f"{len(refspecs)} backup branches updated"


def all_git_repos():
    yield from (Path(git_repo) for git_repo in GIT_REPOS)
    for root in GIT_SEARCH_ROOTS:
        yield from find_git_repos(root)


def backup_vcs():
    failed = []
    for git_repo in all_git_repos():
        if git_repo.name in GIT_REPOS_WITHOUT_OWN_REMOTE:
            continue
        try:
            remote = own_remote(git_repo)
            if remote is None:
                raise RuntimeError("no remote of mine, and not in GIT_REPOS_WITHOUT_OWN_REMOTE")
            print(f"{git_repo}: {backup_git_repo(git_repo, remote)}")
        except (RuntimeError, subprocess.CalledProcessError) as error:
            failed.append(git_repo)
            print(f"{git_repo}: FAILED: {getattr(error, 'stderr', None) or error}", file=sys.stderr)
    if failed:
        print("Failed git repos:", *failed, sep="\n    ", file=sys.stderr)
    return 1 if failed else 0


def backup_all():
    vcs_exit_code = backup_vcs()
    files_exit_code = restic_backup()
    return vcs_exit_code or files_exit_code


def restic_init_secondary():
    if Path(secondary_repo_path()).exists():
        sys.exit(f"Not initializing: {secondary_repo_path()} already exists.")
    require_repo(repo_path(), "--init")
    copy_script_to_drive_of(secondary_repo_path())
    print(f"Initializing new secondary restic repository at {secondary_repo_path()}, "
          f"with the chunker parameters of {repo_path()}")
    return restic("init", "--from-repo", repo_path(), "--from-insecure-no-password", "--copy-chunker-params",
                  repo=secondary_repo_path())


def restic_update_secondary():
    require_repo(repo_path(), "--init")
    require_repo(secondary_repo_path(), "--init-secondary")
    if chunker_polynomial(repo_path()) != chunker_polynomial(secondary_repo_path()):
        sys.exit(f"{secondary_repo_path()} has different chunker parameters than {repo_path()}, "
                 "so copying would not deduplicate and inflate it. Recreate it with --init-secondary.")
    copy_script_to_drive_of(secondary_repo_path())
    print(f"Copying new snapshots from {repo_path()} to {secondary_repo_path()} ...")
    return restic("copy", "--from-repo", repo_path(), "--from-insecure-no-password", "--compression", "off",
                  repo=secondary_repo_path())


def restic_passthrough(restic_args, repo):
    copy_script_to_drive_of(repo)
    return restic(*restic_args, repo=repo)


class Action(enum.Enum):
    BACKUP_ALL = enum.auto()
    BACKUP_FILES = enum.auto()
    BACKUP_VCS = enum.auto()
    INIT = enum.auto()
    RESTIC = enum.auto()
    RESTIC_SECONDARY = enum.auto()
    INIT_SECONDARY = enum.auto()
    UPDATE_SECONDARY = enum.auto()


class StoreResticArgs(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, self.const)
        namespace.restic_args = values


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog=f"(Primary) Repository: {path_for_help(REPO_MARKER_NAME, REPO_DIR)}\n"
                                            f"Secondary repository: {path_for_help(SECONDARY_REPO_MARKER_NAME, SECONDARY_REPO_DIR)}",
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--backup-all", dest="action", action="store_const", const=Action.BACKUP_ALL,
                       help="--backup-vcs, then --backup-files (the default)")
    group.add_argument("--backup-files", dest="action", action="store_const", const=Action.BACKUP_FILES,
                       help="back up files into the repo")
    group.add_argument("--backup-vcs", dest="action", action="store_const", const=Action.BACKUP_VCS,
                       help="push branches, stashes and uncommitted changes of my version-controlled repos "
                            "(currently git only) to backup branches")
    group.add_argument("--init", dest="action", action="store_const", const=Action.INIT,
                       help="create a new, empty repo")
    group.add_argument("--restic", dest="action", action=StoreResticArgs, const=Action.RESTIC,
                       nargs=argparse.REMAINDER, metavar="ARGS",
                       help="run restic with the remaining ARGS")
    group.add_argument("--restic-secondary", dest="action", action=StoreResticArgs, const=Action.RESTIC_SECONDARY,
                       nargs=argparse.REMAINDER, metavar="ARGS",
                       help="run restic with the remaining ARGS on the secondary repo")
    group.add_argument("--init-secondary", dest="action", action="store_const", const=Action.INIT_SECONDARY,
                       help="create a new, empty secondary repo with the primary repo's chunker parameters")
    group.add_argument("--update-secondary", dest="action", action="store_const", const=Action.UPDATE_SECONDARY,
                       help="copy snapshots missing in the secondary repo from the primary repo")
    parser.set_defaults(action=Action.BACKUP_ALL)
    args = parser.parse_args()

    match args.action:
        case Action.BACKUP_ALL:
            exit_code = backup_all()
        case Action.BACKUP_FILES:
            exit_code = restic_backup()
        case Action.BACKUP_VCS:
            exit_code = backup_vcs()
        case Action.INIT:
            exit_code = restic_init()
        case Action.RESTIC:
            exit_code = restic_passthrough(args.restic_args, repo_path())
        case Action.RESTIC_SECONDARY:
            exit_code = restic_passthrough(args.restic_args, secondary_repo_path())
        case Action.INIT_SECONDARY:
            exit_code = restic_init_secondary()
        case Action.UPDATE_SECONDARY:
            exit_code = restic_update_secondary()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()


# Handy restic commands (add --repo and --insecure-no-password as above):
#   restic snapshots                                     list snapshots
#   restic ls latest                                     list files of the latest snapshot
#   restic forget --prune --keep-last 5 --keep-monthly 10 --verbose --dry-run
#   restic prune                                         after aborting a backup
#   rsync --dry-run -a --delete --link-dest="$LAST_SNAPSHOT" "$SRC" "$DEST_NEW_SNAPSHOT"
#
# Restoring. A snapshot is one tree holding the full source paths, with the drive letter
# as top folder: /C/Users/Senso/..., /D/Music/..., /D/new/...  A restore recreates the
# tree below --target, so pick a subtree with "latest:<path>" to avoid extra levels:
#   Full restore (two commands, one per drive):
#     restic restore latest:/C/Users/Senso --target C:\Users\Senso
#     restic restore latest:/S             --target S:\
#   One folder into a temporary place (try --dry-run first):
#     restic restore "latest:/C/Users/Senso/Large/Pictures/Pictures/new/party/Baile Leon II 2026" --target C:\restored
