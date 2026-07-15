"""Lightweight GATE CSE metadata inference for ingested chunks."""

import re


SUBJECT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "DS": ("data structure", "stack", "queue", "tree", "heap", "linked list", "graph"),
    "Algo": ("algorithm", "complexity", "sorting", "dynamic programming", "greedy", "recurrence"),
    "OS": ("operating system", "process", "thread", "deadlock", "paging", "semaphore", "scheduler"),
    "DBMS": ("database", "sql", "transaction", "normalization", "relational", "serializability", "b+ tree"),
    "CN": ("network", "tcp", "udp", "routing", "subnet", "osi", "ip address", "congestion"),
}


def infer_metadata(text: str, filename: str) -> dict[str, str]:
    """Infer subject, topic, and difficulty using deterministic domain keywords."""
    haystack = f"{filename} {text}".lower()
    scores = {
        subject: sum(haystack.count(keyword) for keyword in keywords)
        for subject, keywords in SUBJECT_KEYWORDS.items()
    }
    subject = max(scores, key=scores.get) if max(scores.values(), default=0) else "Unknown"
    matched = [keyword for keyword in SUBJECT_KEYWORDS.get(subject, ()) if keyword in haystack]
    topic = matched[0].title() if matched else "General"

    complexity_hits = len(re.findall(r"\b(prove|derive|analy[sz]e|worst.case|NP.complete)\b", haystack))
    difficulty = "hard" if complexity_hits >= 2 else "medium" if complexity_hits == 1 else "easy"
    return {"subject": subject, "topic": topic, "difficulty": difficulty}

