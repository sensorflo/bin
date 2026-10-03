# - In raw editor, mark all files in source folder with label organge (1)
# - Run scripty. It will mark all xmp files in the source folder that occur in the export folder with label red (0)
# - In raw editor, remove all red labels
# - The images labeled orange are the ones not yet exported

from pathlib import Path
import os
import sys

SOURCE_FOLDER = "C:/Users/senso/Large/Pictures/Pictures/new/party/New Healing 2024"
EXPORT_FOLDER = "C:/Users/senso/Large/Pictures/Pictures/generated/party/New Healing 2024"

def mark_as_exported(xmp_path):
    with open(xmp_path, "r", encoding="utf-8") as f:
        text = f.read()

    text = text.replace("<rdf:li>1</rdf:li>", "<rdf:li>0</rdf:li>")

    with open(xmp_path, "w", encoding="utf-8") as f:
        f.write(text)

def main():
    exported_stems = {
        os.path.splitext(filename)[0].lower()
        for filename in os.listdir(EXPORT_FOLDER)
        if filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg")
    }

    source_folder = Path(SOURCE_FOLDER)
    for filename in os.listdir(SOURCE_FOLDER):
        stem = filename.split(".", 1)[0].lower()
        ext = filename.rsplit(".", 1)[-1].lower()
        if not ext == "xmp":
            continue
        if stem in exported_stems:
            for xmp_path in source_folder.glob(f"{stem}.*.xmp"):
                mark_as_exported(xmp_path)

if __name__ == "__main__":
    main()
