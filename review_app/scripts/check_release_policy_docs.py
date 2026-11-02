"""Check documented release gates match the authoritative JSON register."""
import json
from pathlib import Path

try:
    from .check_release_gates import REQUIRED, inspect_gates
except ImportError:
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
    if text.count(marker) != 1:
        raise ValueError("documentation requires one authoritative gate inventory")
    inventory = text.split(marker, 1)[1].split("\n## ", 1)[0]
    for item in data["requirements"]:
        gate = item["id"]
        if gate not in REQUIRED or inventory.count("`" + gate + "`") != 1:
            raise ValueError("documented gate missing or duplicated: " + gate)
    if len(data["requirements"]) != len(REQUIRED):
        raise ValueError("release-gate count differs from policy")
    return {"blocked": True, "documented_gates": len(REQUIRED)}


def main():
    root = Path(__file__).resolve().parents[2]
    print(json.dumps(inspect_policy_docs(root), indent=2))


if __name__ == "__main__":
    main()
