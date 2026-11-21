
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from pydantic import ValidationError

from schemas import Resume


load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")

if not API_KEY:
    raise SystemExit("Missing OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
    timeout=30.0,
    max_retries=0,
)

INPUT_DIR = Path("sample_docs")
OUTPUT_DIR = Path("output")

MAX_ATTEMPTS = 3


def read_document(path):
    return path.read_text(encoding="utf-8")


def process_documents():
    files = sorted(INPUT_DIR.glob("*.txt"))

    if not files:
        print("No resume files found.")
        return

    results = []

    for file_path in files:
        print(f"\nProcessing: {file_path.name}")

        try:
            document = read_document(file_path)

            resume = extract_with_retries(document)

            output_path = (
                OUTPUT_DIR / f"{file_path.stem}.json"
            )

            save_json(resume, output_path)

            print(f"Saved: {output_path}")

            results.append({
                "file": file_path.name,
                "status": "success",
                "error": None
            })

        except (OpenAIError, ValueError, OSError) as error:
            print(f"Failed: {file_path.name}")
            print(f"Reason: {type(error).__name__}")

            results.append({
                "file": file_path.name,
                "status": "failed",
                "error": str(error)
            })

    return results



def parse_and_validate(raw_output):
    data = json.loads(raw_output)
    return Resume.model_validate(data)


def extract_with_retries(document_text):
    instructions = """
Extract the following resume fields:

name, email, phone, skills,
experience_years, education.

Return only a valid JSON object.

Rules:
- Include every required field.
- Use null for missing scalar values.
- Use an empty list for missing skills.
- Skills must be a list of strings.
- Experience must be non-negative or null.
- Do not invent information.
- Do not include Markdown code fences.
"""

    messages = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": document_text},
    ]

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\nExtraction attempt {attempt}/{MAX_ATTEMPTS}")

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0,
        )

        raw_output = response.choices[0].message.content

        if not raw_output:
            raw_output = ""

        try:
            resume = parse_and_validate(raw_output)

            print("Validation successful!")
            return resume

        except (json.JSONDecodeError, ValidationError) as error:
            print(f"Validation failed: {type(error).__name__}")

            if attempt == MAX_ATTEMPTS:
                raise ValueError(
                    f"Extraction failed after {MAX_ATTEMPTS} attempts"
                ) from error

            messages.append({
                "role": "assistant",
                "content": raw_output
            })

            messages.append({
                "role": "user",
                "content": (
                    "Your previous output was invalid.\n"
                    f"Validation error:\n{error}\n\n"
                    "Correct the JSON using only information "
                    "from the original resume. "
                    "Return only the corrected JSON object."
                )
            })

    raise RuntimeError("Unexpected retry-loop termination")


def save_json(resume, path):
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        resume.model_dump_json(indent=2),
        encoding="utf-8",
    )



def main():
    results = process_documents()

    if not results:
        return

    success_count = sum(
        1 for result in results
        if result["status"] == "success"
    )

    failed_count = len(results) - success_count

    print("\n===== BATCH SUMMARY =====")
    print(f"Total files: {len(results)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failed_count}")
    print("=========================")


if __name__ == "__main__":
    main()

