R"""Back up my home folder and SD card with restic.

Ensure Defender is turned off, or at least that restic.exe and the backup folder
are excluded from scanning.

To check what actually ends up in the backup, run backup_audit.py.
"""
# For usage, run with --help

import argparse
import enum
import functools
import os
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
# The repo lives on whichever drive has a REPO_MARKER_NAME file in its root.
REPO_MARKER_NAME = ".backup-destination"
REPO_DIR = R"Backup\restic-backup-dell-xps-15-home-folder"

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
def repo_path():
    drives = [f"{drive_letter}:\\" for drive_letter in string.ascii_uppercase
              if os.path.exists(f"{drive_letter}:\\{REPO_MARKER_NAME}")]
    if len(drives) != 1:
        sys.exit(f"Expected exactly one drive with a {REPO_MARKER_NAME} file in its root, "
                 f"found: {', '.join(drives) or 'none'}")
    return drives[0] + ":\\" + REPO_DIR


def restic(*args):
    """Run restic with the given arguments, return its exit code."""
    return subprocess.run(["restic", *args, "--repo", repo_path(), "--insecure-no-password"]).returncode


def restic_init():
    if Path(repo_path()).exists():
        sys.exit(f"Not initializing: {repo_path()} already exists.")
    print(f"Initializing new restic repository at {repo_path()}")
    return restic("init", "--compression", "off")


def restic_backup():
    if not (Path(repo_path()) / "config").exists():
        sys.exit(f"No restic repository at {repo_path()}. "
                 "To create a new one: python backup.py --init")
    if not Path(SD_MARKER_PATH).exists():
        sys.exit(f"SD card not found: {SD_MARKER_PATH} is missing (card not inserted, or a different "
                 "drive letter?). Not backing up, since the snapshot would be incomplete.")
    print(f"Starting backup of {', '.join(SOURCE_PATHS)} ...")
    excludes = [f"--iexclude={pattern}" for pattern in EXCLUDES]
    return restic("backup", *SOURCE_PATHS, *excludes, "--compression", "off", "--verbose")


class Action(enum.Enum):
    BACKUP = enum.auto()
    INIT = enum.auto()
    RESTIC = enum.auto()


class StoreResticArgs(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, Action.RESTIC)
        namespace.restic_args = values


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog=f"Repository: <drive with {REPO_MARKER_NAME}>:\\{REPO_DIR}",
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--backup", dest="action", action="store_const", const=Action.BACKUP,
                       help="back up (the default)")
    group.add_argument("--init", dest="action", action="store_const", const=Action.INIT,
                       help="create a new, empty repo")
    group.add_argument("--restic", dest="action", action=StoreResticArgs, nargs=argparse.REMAINDER, metavar="ARGS",
                       help="run restic with the remaining ARGS")
    parser.set_defaults(action=Action.BACKUP)
    args = parser.parse_args()

    match args.action:
        case Action.BACKUP:
            exit_code = restic_backup()
        case Action.INIT:
            exit_code = restic_init()
        case Action.RESTIC:
            exit_code = restic(*args.restic_args)
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
