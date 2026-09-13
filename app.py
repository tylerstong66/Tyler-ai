def memory_write_intent_present(message):
    text = normalized(message)

    if any(
        term in text
        for term in [
            "do not save",
            "don't save",
            "dont save",
            "do not remember",
            "don't remember",
            "dont remember",
            "no memory",
            "do not store",
            "don't store",
            "dont store",
        ]
    ):
        return False

    direct_terms = [
        "remember that",
        "remember this",
        "remember the recommendation",
        "remember my choice",
        "save to memory",
        "save this",
        "save that",
        "save the result",
        "save the results",
        "store this",
        "don't forget",
        "do not forget",
        "create a memory",
        "create memory",
        "add to memory",
        "add this to memory",
        "put this in memory",
        "store in memory",
        "store this in memory",
        "save it in memory",
        "save it to memory",
        "before saving",
        "before you save",
    ]

    if any(term in text for term in direct_terms):
        return True

    if (
        "memory" in text
        and any(
            term in text
            for term in [
                "save",
                "saving",
                "store",
                "storing",
                "remember",
                "record",
                "create",
            ]
        )
    ):
        return True

    return False
