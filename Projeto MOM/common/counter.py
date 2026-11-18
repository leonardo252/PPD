import re


def normalize_keywords(raw_keywords):
    if isinstance(raw_keywords, str):
        candidates = raw_keywords.replace(";", ",").split(",")
    else:
        candidates = raw_keywords

    result = []
    seen = set()
    for value in candidates:
        keyword = str(value).strip()
        identity = keyword.casefold()
        if keyword and identity not in seen:
            seen.add(identity)
            result.append(keyword)
    return result


def count_keywords(text, keywords):
    counts = {}
    for keyword in keywords:
        pattern = r"(?<!\w){}(?!\w)".format(re.escape(keyword))
        counts[keyword] = len(re.findall(pattern, text, flags=re.IGNORECASE))
    return counts
