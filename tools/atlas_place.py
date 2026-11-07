#!/usr/bin/env python3
"""Add and remove league cities in the Softmax Atlas geography directory."""

import argparse
import json
import sys
from pathlib import Path

from atlas_spot import parse


def fail(message):
    print(f"atlas_place: {message}", file=sys.stderr)
    sys.exit(2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--geography", required=True, type=Path)
    parser.add_argument("--add", default="[]", help="JSON array of city entries")
    parser.add_argument("--drop", default="", help="comma-separated slugs to remove")
    args = parser.parse_args()

    regions, _, _ = parse(args.geography)
    path = args.geography / "cities.json"
    cities = json.loads(path.read_text(encoding="utf-8"))
    adds = json.loads(args.add or "[]")
    if not isinstance(adds, list):
        fail("--add must be a JSON array of entries")

    for entry in adds:
        if not isinstance(entry, list) or len(entry) < 5:
            fail(f"entry needs at least [slug,label,x,y,region]: {entry!r}")
        region = entry[4]
        if region not in regions:
            fail(f"{entry[0]}: unknown region {region!r}")
        x0, y0, x1, y1 = regions[region]["box"]
        if not (x0 <= float(entry[2]) <= x1 and y0 <= float(entry[3]) <= y1):
            fail(f"{entry[0]}: ({entry[2]},{entry[3]}) is outside the {region} box")

    changed = False
    drops = {slug.strip() for slug in args.drop.split(",") if slug.strip()}
    retained = [city for city in cities if city[0] not in drops]
    if len(retained) != len(cities):
        cities = retained
        changed = True

    for entry in adds:
        if any(city[0] == entry[0] for city in cities):
            continue
        city = [entry[0], entry[1], int(entry[2]), int(entry[3]), entry[4]]
        territory = entry[5] if len(entry) > 5 else None
        anchor = entry[6] if len(entry) > 6 else None
        if anchor:
            city.extend([territory or None, anchor])
        elif territory:
            city.append(territory)
        same = [index for index, existing in enumerate(cities) if existing[4] == city[4]]
        cities.insert(same[-1] + 1 if same else len(cities), city)
        changed = True
        print(f"atlas_place: added {city[0]} at {city[2]},{city[3]} in {city[4]}")

    if changed:
        path.write_text(json.dumps(cities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        print("atlas_place: no change")


if __name__ == "__main__":
    main()
