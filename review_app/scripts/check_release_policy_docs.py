"""Check documented release gates match the authoritative JSON register."""
import json
import re
from pathlib import Path

if __package__:
    from .check_release_gates import REQUIRED, inspect_gates
else:
    from check_release_gates import REQUIRED, inspect_gates


def inspect_policy_docs(root):
    root = Path(root)
    register = root / "docs" / "release-gates.json"
    documentation = root / "docs" / "RELEASE_GATES.md"
    text = documentation.read_text(encoding="utf-8")
    data = json.loads(register.read_text(encoding="utf-8"))
    result = inspect_gates(register)
    if not result["blocked"]:
        raise ValueError("documented production policy must remain blocked in CI")
    if "Production release status: BLOCKED" not in text:
        raise ValueError("documentation lacks explicit blocked release status")
    marker = "## Authoritative gate inventory"
    lines = text.splitlines()
    headings = [i for i, line in enumerate(lines) if line.strip() == marker]
    if len(headings) != 1:
        raise ValueError("documentation requires one authoritative gate inventory")
    start = headings[0] + 1
    end = next((i for i in range(start, len(lines))
                if lines[i].startswith("## ")), len(lines))
    inventory = "\n".join(lines[start:end])
    documented = re.findall(r"`([a-z][a-z0-9_]+)`", inventory)
    for gate in REQUIRED:
        if documented.count(gate) != 1:
            raise ValueError("documented gate missing or duplicated: " + gate)
    unexpected = sorted(set(documented) - REQUIRED)
    if unexpected:
        raise ValueError("unexpected gate identifiers in inventory: " + ", ".join(unexpected))
    if len(data["requirements"]) != len(REQUIRED):
        raise ValueError("release-gate count differs from policy")
    return {"blocked": True, "documented_gates": len(REQUIRED)}


def main():
    root = Path(__file__).resolve().parents[2]
    print(json.dumps(inspect_policy_docs(root), indent=2))


if __name__ == "__main__":
    main()
