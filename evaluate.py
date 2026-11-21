import json
from pathlib import Path

from pydantic import ValidationError
from schemas import Resume


INPUT_DIR = Path("sample_docs")
TRUTH_DIR = Path("ground_truth")
OUTPUT_DIR = Path("output")

FIELDS = list(Resume.model_fields)


def load_json(path):
    data = json.loads(
        path.read_text(encoding="utf-8")
    )
    return Resume.model_validate(data)


def normalize(value):
    if isinstance(value, str):
        return " ".join(value.casefold().split())

    if isinstance(value, list):
        return sorted(normalize(item) for item in value)

    return value


def compare_resumes(expected, predicted):
    expected_data = expected.model_dump()
    predicted_data = predicted.model_dump()

    field_results = {}

    for field in FIELDS:
        field_results[field] = (
            normalize(expected_data[field])
            == normalize(predicted_data[field])
        )

    return field_results


def evaluate():
    files = sorted(INPUT_DIR.glob("*.txt"))

    if len(files) < 20:
        raise ValueError(
            "Evaluation requires at least 20 resumes. "
            f"Found {len(files)}."
        )

    total_fields = len(files) * len(FIELDS)
    correct_fields = 0
    perfect_documents = 0
    failed_documents = 0

    field_correct = {
        field: 0 for field in FIELDS
    }

    failures = []

    for file_path in files:
        name = file_path.stem
        truth_path = TRUTH_DIR / f"{name}.json"
        output_path = OUTPUT_DIR / f"{name}.json"

        if not truth_path.exists():
            raise FileNotFoundError(
                f"Missing ground truth: {truth_path}"
            )

        expected = load_json(truth_path)

        try:
            predicted = load_json(output_path)

        except (
            FileNotFoundError,
            json.JSONDecodeError,
            ValidationError,
            OSError,
        ) as error:
            failed_documents += 1

            failures.append({
                "file": file_path.name,
                "type": "extraction_failure",
                "details": type(error).__name__,
            })
            continue

        comparisons = compare_resumes(
            expected, predicted
        )

        document_correct = 0

        for field, is_correct in comparisons.items():
            if is_correct:
                correct_fields += 1
                field_correct[field] += 1
                document_correct += 1

            else:
                failures.append({
                    "file": file_path.name,
                    "type": "field_mismatch",
                    "field": field,
                    "expected": getattr(expected, field),
                    "predicted": getattr(predicted, field),
                })

        if document_correct == len(FIELDS):
            perfect_documents += 1

    report = {
        "total_documents": len(files),
        "failed_documents": failed_documents,
        "perfect_documents": perfect_documents,
        "field_accuracy": round(
            correct_fields / total_fields * 100, 2
        ),
        "document_accuracy": round(
            perfect_documents / len(files) * 100, 2
        ),
        "per_field_accuracy": {
            field: round(
                count / len(files) * 100, 2
            )
            for field, count in field_correct.items()
        },
        "failures": failures,
    }

    print(json.dumps(
        report, indent=2, ensure_ascii=False
    ))

    Path("evaluation_report.json").write_text(
        json.dumps(
            report, indent=2, ensure_ascii=False
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    evaluate()
