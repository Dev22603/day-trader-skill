#!/usr/bin/env python3
"""The course keeper for trader-learn: which lesson is next, what a word means,
what is done. Standard library only, no network. It teaches nothing itself:
Claude does the teaching from what this prints.

    python3 learn.py list                   # the whole course, with what is done
    python3 learn.py next                   # the next lesson that is not done
    python3 learn.py show H3                # one lesson
    python3 learn.py done H3 --score 2/3    # mark it done (the check questions: 2 right of 3)
    python3 learn.py term "gross profit"    # a word from the glossary (the closest match)

The lessons are in course.md and the words in glossary.md, next to this file.
Both are plain text you can read and edit. Progress is kept in
trader/state/learn.json (--state PATH).

A lesson in course.md:

    ### H3 Position size: how many shares
    Goal: one line.
    - a point
    - another point
    Example: one worked example in rupees.
    Check:
    1. A question? :: The answer
    In the pack: where this shows up in the other skills.

A word in glossary.md:

    - **gross profit** (gross): what it means, in one or two plain sentences. Lesson A2.

Exit codes: 0 = printed what was asked, 1 = nothing to print (the course is
finished, the lesson or the word is not there) or an error.
"""

import argparse
import datetime
import difflib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COURSE = os.path.join(HERE, "course.md")
GLOSSARY = os.path.join(HERE, "glossary.md")


class LearnError(Exception):
    pass


def read_text(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError as e:
        raise LearnError("could not read %s: %s" % (path, e))


def parse_course(text):
    """course.md -> [lesson], in order. A lesson: id, title, module, goal, points,
    example, checks [(question, answer)], pack."""
    lessons, module, cur, in_check = [], "", None, False
    for raw in text.splitlines():
        line = raw.strip()
        m = re.match(r"^##\s+(\S+)\s+(.+)$", line)
        if m and not line.startswith("###"):
            module, cur = "%s %s" % (m.group(1), m.group(2)), None
            continue
        m = re.match(r"^###\s+([A-Z]\d+)\s+(.+)$", line)
        if m:
            cur = {"id": m.group(1), "title": m.group(2), "module": module, "goal": "", "points": [],
                   "example": "", "checks": [], "pack": ""}
            lessons.append(cur)
            in_check = False
            continue
        if cur is None or not line:
            continue
        if line.startswith("Goal:"):
            cur["goal"] = line[5:].strip()
        elif line.startswith("Example:"):
            cur["example"], in_check = line[8:].strip(), False
        elif line.startswith("In the pack:"):
            cur["pack"], in_check = line[12:].strip(), False
        elif line == "Check:":
            in_check = True
        elif in_check and re.match(r"^\d+\.\s", line):
            q, _, a = re.sub(r"^\d+\.\s+", "", line).partition("::")
            cur["checks"].append((q.strip(), a.strip()))
        elif line.startswith("- "):
            cur["points"].append(line[2:].strip())
    return lessons


def parse_glossary(text):
    """glossary.md -> [{"term", "aliases", "meaning", "lesson"}]."""
    out = []
    for line in text.splitlines():
        m = re.match(r"^- \*\*(.+?)\*\*(?: \((.+?)\))?: (.+)$", line.strip())
        if not m:
            continue
        meaning = m.group(3).strip()
        ref = re.search(r"Lesson ([A-Z]\d+)\.?$", meaning)
        out.append({"term": m.group(1).strip(), "aliases": [a.strip() for a in (m.group(2) or "").split(",") if a.strip()],
                    "meaning": meaning, "lesson": ref.group(1) if ref else None})
    return out


def squeeze(word):
    """stop-loss, Stop Loss and stoploss are the same word."""
    return re.sub(r"[^a-z0-9]", "", str(word).lower())


def find_term(words, asked):
    """(entry, how) with how = "exact" or "close", or (None, [near misses])."""
    keys = {}
    for w in words:
        for name in [w["term"]] + w["aliases"]:
            keys.setdefault(squeeze(name), w)
    k = squeeze(asked)
    if k in keys:
        return keys[k], "exact"
    close = difflib.get_close_matches(k, list(keys), n=3, cutoff=0.75)
    if close:
        return keys[close[0]], "close"
    return None, [keys[c]["term"] for c in difflib.get_close_matches(k, list(keys), n=3, cutoff=0.5)]


def load_state(path):
    if not path or not os.path.exists(path):
        return {"done": {}}
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except ValueError as e:
        raise LearnError("%s is not valid JSON: %s" % (path, e))
    if not isinstance(doc, dict) or not isinstance(doc.get("done", {}), dict):
        raise LearnError("%s is not a progress file" % path)
    doc.setdefault("done", {})
    return doc


def save_state(path, doc):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, path)


def lesson_lines(l):
    """A lesson for Claude to teach from. The answers are for Claude: ask the question, wait, then compare."""
    out = ["%s  %s" % (l["id"], l["title"]), "Module: %s" % l["module"], "Goal: %s" % l["goal"], "Teach:"]
    out += ["  - " + p for p in l["points"]]
    if l["example"]:
        out.append("Example: " + l["example"])
    out.append("Check (ask one at a time, wait for the answer, never show the answer first):")
    for i, (q, a) in enumerate(l["checks"], 1):
        out.append("  %d. %s" % (i, q))
        out.append("     answer: %s" % a)
    if l["pack"]:
        out.append("In the pack: " + l["pack"])
    out.append("When the checks are done: learn.py done %s --score RIGHT/%d" % (l["id"], len(l["checks"])))
    return out


def cmd_list(a, lessons, state):
    done = state["done"]
    module = None
    for l in lessons:
        if l["module"] != module:
            module = l["module"]
            print(module)
        rec = done.get(l["id"])
        mark = "[x]" if rec else "[ ]"
        score = ("  (%s)" % rec["score"]) if rec and rec.get("score") else ""
        print("  %s %-3s %s%s" % (mark, l["id"], l["title"], score))
    n = sum(1 for l in lessons if l["id"] in done)
    print("%d of %d lessons done." % (n, len(lessons)))
    return 0


def cmd_next(a, lessons, state):
    for l in lessons:
        if l["id"] not in state["done"]:
            print("\n".join(lesson_lines(l)))
            return 0
    print("The course is finished: all %d lessons are done. learn.py list shows them; learn.py show ID repeats one."
          % len(lessons))
    return 1


def pick(lessons, lesson_id):
    for l in lessons:
        if l["id"] == str(lesson_id).upper():
            return l
    raise LearnError("there is no lesson %s (learn.py list shows the lessons)" % lesson_id)


def cmd_show(a, lessons, state):
    print("\n".join(lesson_lines(pick(lessons, a.id))))
    return 0


def cmd_done(a, lessons, state):
    l = pick(lessons, a.id)
    if a.score and not re.match(r"^\d+/\d+$", a.score):
        raise LearnError("--score wants right/asked, like 2/3")
    rec = {"at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    if a.score:
        rec["score"] = a.score
    state["done"][l["id"]] = rec
    save_state(a.state, state)
    left = [x for x in lessons if x["id"] not in state["done"]]
    print("Done: %s %s%s." % (l["id"], l["title"], (" (%s)" % a.score) if a.score else ""))
    print("Next: %s %s." % (left[0]["id"], left[0]["title"]) if left else "That was the last lesson: the course is finished.")
    return 0


def cmd_term(a, lessons, state):
    words = parse_glossary(read_text(GLOSSARY))
    hit, how = find_term(words, a.word)
    if hit is None:
        print("\"%s\" is not in the glossary.%s Explain it in plain words yourself, and say that it is your own "
              "explanation, not the course's." % (a.word, (" Close: " + ", ".join(how) + ".") if how else ""))
        return 1
    if how == "close":
        print("Closest word in the glossary to \"%s\":" % a.word)
    print("%s: %s" % (hit["term"], hit["meaning"]))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="The course keeper (trader-learn): lessons, progress and a glossary.")
    ap.add_argument("--state", default="trader/state/learn.json", help="where your progress is kept")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("list", help="the whole course, with what is done")
    sub.add_parser("next", help="the next lesson that is not done")
    p = sub.add_parser("show", help="one lesson")
    p.add_argument("id")
    p = sub.add_parser("done", help="mark a lesson done")
    p.add_argument("id")
    p.add_argument("--score", help="check questions right/asked, like 2/3")
    p = sub.add_parser("term", help="what a word means")
    p.add_argument("word")
    a = ap.parse_args(argv)
    if not a.cmd:
        ap.print_help()
        return 1
    try:
        lessons = parse_course(read_text(COURSE))
        state = load_state(a.state)
        return {"list": cmd_list, "next": cmd_next, "show": cmd_show, "done": cmd_done, "term": cmd_term}[a.cmd](
            a, lessons, state)
    except LearnError as e:
        print("learn.py: %s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
