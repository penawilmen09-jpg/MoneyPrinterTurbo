import json, re
def load(path):
    d = json.load(open(path)); a = d["alignment"]
    ch, st, en = a["characters"], a["character_start_times_seconds"], a["character_end_times_seconds"]
    words, cur, s, e = [], "", None, None
    for c, t0, t1 in zip(ch, st, en):
        if c.isspace():
            if cur: words.append((cur, s, e)); cur, s = "", None
        else:
            if s is None: s = t0
            cur += c; e = t1
    if cur: words.append((cur, s, e))
    return words
if __name__ == "__main__":
    import sys
    for i, w in enumerate(load(sys.argv[1])): print(i, w[0], round(w[1],2), round(w[2],2))
