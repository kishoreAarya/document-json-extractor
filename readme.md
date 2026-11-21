# Document-to-JSON Extractor

A Python application that uses an LLM through OpenRouter to extract structured information from resumes.

## Features

- Resume text extraction using an LLM
- JSON parsing
- Pydantic schema validation
- Bounded retries with validation feedback
- Batch processing of multiple resumes
- Per-document success and failure reporting
- Evaluation against manually verified ground-truth data
- Automated tests with pytest

## Tech Stack

- Python
- OpenRouter API
- OpenAI-compatible Python SDK
- Pydantic v2
- pytest

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your OpenRouter API key.

## Run Extraction

```bash
python main.py
```

Text resumes are read from `sample_docs/`.

Validated JSON files are saved in `output/`.

## Run Evaluation

Prepare at least 20 resumes and their manually verified JSON answers in `ground_truth/`.

Run extraction on a clean output directory, then:

```bash
python evaluate.py
```

The evaluation report includes:

- Field-level accuracy
- Exact-document accuracy
- Extraction failures
- Per-field accuracy
- Mismatched extracted values

## Run Automated Tests

```bash
python -m pytest -v
```

The unit tests use mock API responses and do not require actual LLM inference.

## Limitations

- The current implementation processes plain-text resumes, not PDFs or scanned documents.
- Pydantic validates structure but cannot guarantee factual correctness.
- Free LLM availability and behavior can vary.
- Retries for invalid outputs are limited.
- The evaluation compares fields using basic normalization.
- The extractor processes documents sequentially.

## Learning Outcomes

This project demonstrates structured LLM extraction, schema validation, bounded correction loops, batch processing, and measurable evaluation.