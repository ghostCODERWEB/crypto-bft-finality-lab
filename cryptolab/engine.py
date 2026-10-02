"""Analyze block ancestry, weighted voting certificates, equivocation and conflicting finalized branches."""

from .validation import integer, identifier
from collections import defaultdict


def analyze(data):
    validators = {
        identifier(v): integer(w, minimum=1) for v, w in data["validators"].items()
    }
    total = sum(validators.values())
    threshold = 2 * total // 3 + 1
    if not validators:
        raise ValueError("validators required")
    blocks = {}
    for b in data["blocks"]:
        key = identifier(b["id"])
        if key in blocks:
            raise ValueError("duplicate block")
        height = integer(b["height"])
        parent = b["parent"]
        if height == 0:
            if parent is not None or any(x["height"] == 0 for x in blocks.values()):
                raise ValueError("unique genesis required")
        elif parent not in blocks or blocks[parent]["height"] + 1 != height:
            raise ValueError("missing or inconsistent parent")
        blocks[key] = {"height": height, "parent": parent}
    votes = defaultdict(set)
    seen = defaultdict(set)
    duplicates = []
    for vote in data["votes"]:
        validator = identifier(vote["validator"])
        block = identifier(vote["block"])
        round = integer(vote["round"])
        if validator not in validators or block not in blocks:
            raise ValueError("unknown vote identity")
        key = (blocks[block]["height"], round, validator)
        if block in seen[key]:
            duplicates.append(vote)
            continue
        seen[key].add(block)
        votes[(block, round)].add(validator)
    equivocations = [
        {"height": h, "round": r, "validator": v, "blocks": sorted(bs)}
        for (h, r, v), bs in sorted(seen.items())
        if len(bs) > 1
    ]
    certificates = []
    finalized = set()
    for (block, round), voters in sorted(votes.items()):
        weight = sum(validators[v] for v in voters)
        if weight >= threshold:
            certificates.append(
                {
                    "block": block,
                    "round": round,
                    "weight": weight,
                    "validators": sorted(voters),
                }
            )
            current = block
            while current is not None:
                finalized.add(current)
                current = blocks[current]["parent"]
    heights = defaultdict(list)
    for block in finalized:
        heights[blocks[block]["height"]].append(block)
    conflicts = [
        {"height": h, "blocks": sorted(bs)}
        for h, bs in sorted(heights.items())
        if len(bs) > 1
    ]
    faulty = {e["validator"] for e in equivocations}
    fault_weight = sum(validators[v] for v in faulty)
    return {
        "total_weight": total,
        "quorum_threshold": threshold,
        "certificates": certificates,
        "finalized_blocks": sorted(finalized),
        "equivocations": equivocations,
        "equivocating_weight": fault_weight,
        "conflicts": conflicts,
        "duplicate_votes": len(duplicates),
        "safety_violation": bool(conflicts),
    }
