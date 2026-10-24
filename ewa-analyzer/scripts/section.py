#!/usr/bin/env python3
"""Print one section of the extracted EWA text, so a long report can be read in small pieces.

Usage:
    python section.py ewa_extract "Program Errors"        # first heading containing the text
    python section.py ewa_extract "Security" --level 1    # only top-level headings
    python section.py ewa_extract --list                  # list all headings with levels
"""
import argparse, json, os, sys

ap = argparse.ArgumentParser()
ap.add_argument("folder")
ap.add_argument("title", nargs="?")
ap.add_argument("--level", type=int)
ap.add_argument("--list", action="store_true")
ap.add_argument("--max-lines", type=int, default=400)
a = ap.parse_args()
idx = json.load(open(os.path.join(a.folder, "ewa_index.json"), encoding="utf-8"))
lines = open(os.path.join(a.folder, "ewa_text.md"), encoding="utf-8").read().split("\n")
if a.list or not a.title:
    for h in idx:
        print("%s%s  (line %d)" % ("  " * (h["level"] - 1), h["title"], h["line"]))
    sys.exit(0)
for i, h in enumerate(idx):
    if a.title.lower() in h["title"].lower() and (a.level is None or h["level"] == a.level):
        end = len(lines)
        for h2 in idx[i + 1:]:
            if h2["level"] <= h["level"]:
                end = h2["line"] - 1
                break
        chunk = lines[h["line"] - 1:end]
        print("\n".join(chunk[:a.max_lines]))
        if len(chunk) > a.max_lines:
            print("... [%d more lines, raise --max-lines or read subsections]" % (len(chunk) - a.max_lines))
        sys.exit(0)
sys.exit("No heading contains %r. Use --list." % a.title)
