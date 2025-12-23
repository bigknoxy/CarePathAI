#!/usr/bin/env python3
from pathlib import Path
import json
import random
import importlib.util
from datetime import date, timedelta

# Import data_paths module directly
data_paths_path = Path(__file__).resolve().parents[1] / "utils" / "data_paths.py"
spec = importlib.util.spec_from_file_location("data_paths", data_paths_path)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load data_paths from {data_paths_path}")
data_paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data_paths)
get_data_paths = data_paths.get_data_paths

# Get data directory from helper module
OUT_DIR, _ = get_data_paths()
OUT_DIR.mkdir(parents=True, exist_ok=True)

FIRST_NAMES = ["John", "Jane", "Alex", "Maria", "Wei", "Priya"]
LAST_NAMES = ["Doe", "Smith", "Patel", "Chen", "Gonzalez", "Khan"]
CONDITIONS = [
    "hypertension",
    "diabetes",
    "anxiety",
    "depression",
    "asthma",
    "pregnancy",
]


def random_dob():
    start = date(1940, 1, 1)
    end = date(2010, 1, 1)
    delta = end - start
    days = random.randrange(delta.days)
    return (start + timedelta(days=days)).isoformat()


def gen_patient(i):
    fn = random.choice(FIRST_NAMES)
    ln = random.choice(LAST_NAMES)
    dob = random_dob()
    mrn = f"MRN{i:03d}"
    conditions = random.sample(CONDITIONS, k=random.randint(1, 2))

    notes = []
    for c in conditions:
        notes.append(f"Patient has a history of {c}. Symptoms include ...")

    patient = {
        "id": i,
        "firstName": fn,
        "lastName": ln,
        "dateOfBirth": dob,
        "medicalRecordNumber": mrn,
        "conditions": conditions,
        "notes": "\n".join(notes),
    }
    return patient


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--output", type=str, default=str(OUT_DIR))
    args = parser.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    for i in range(1, args.count + 1):
        p = gen_patient(i)
        fname = out / f"patient_{i:03d}.json"
        with open(fname, "w") as f:
            json.dump(p, f, indent=2)

    print(f"Generated {args.count} synthetic patients to {out}")
