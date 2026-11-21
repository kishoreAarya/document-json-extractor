
import json
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

import main
from schemas import Resume
from evaluate import compare_resumes


VALID_DATA = {
    "name": "Rahul Sharma",
    "email": "rahul@example.com",
    "phone": None,
    "skills": ["Python", "SQL"],
    "experience_years": 3,
    "education": "B.Tech",
}


def test_valid_resume():
    resume = Resume.model_validate(VALID_DATA)

    assert resume.name == "Rahul Sharma"
    assert resume.experience_years == 3
    assert resume.skills == ["Python", "SQL"]


def test_invalid_email():
    data = {
        **VALID_DATA,
        "email": "not-an-email"
    }

    with pytest.raises(ValidationError):
        Resume.model_validate(data)


def test_negative_experience():
    data = {
        **VALID_DATA,
        "experience_years": -5
    }

    with pytest.raises(ValidationError):
        Resume.model_validate(data)


def test_invalid_json():
    raw_output = '{"name": "Rahul"'

    with pytest.raises(json.JSONDecodeError):
        main.parse_and_validate(raw_output)


def fake_response(text):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=text)
            )
        ]
    )


def test_retry_then_success(monkeypatch):
    responses = [
        '{"name":',
        json.dumps(VALID_DATA)
    ]

    calls = []

    def mock_create(**kwargs):
        calls.append(kwargs)
        index = len(calls) - 1
        return fake_response(responses[index])

    monkeypatch.setattr(
        main.client.chat.completions,
        "create",
        mock_create
    )

    result = main.extract_with_retries(
        "Rahul Sharma, Python developer"
    )

    assert result.name == "Rahul Sharma"
    assert len(calls) == 2


def test_retry_limit(monkeypatch):
    calls = []

    def mock_create(**kwargs):
        calls.append(kwargs)
        return fake_response("invalid json")

    monkeypatch.setattr(
        main.client.chat.completions,
        "create",
        mock_create
    )

    with pytest.raises(
        ValueError,
        match="Extraction failed after"
    ):
        main.extract_with_retries("Sample resume")

    assert len(calls) == main.MAX_ATTEMPTS


def test_batch_processing(monkeypatch, tmp_path):
    input_dir = tmp_path / "sample_docs"
    output_dir = tmp_path / "output"

    input_dir.mkdir()

    (input_dir / "resume_01.txt").write_text(
        "Rahul Sharma",
        encoding="utf-8"
    )

    (input_dir / "resume_02.txt").write_text(
        "Another candidate",
        encoding="utf-8"
    )

    monkeypatch.setattr(
        main,
        "INPUT_DIR",
        input_dir
    )

    monkeypatch.setattr(
        main,
        "OUTPUT_DIR",
        output_dir
    )

    def mock_extract(document):
        if document == "Another candidate":
            raise ValueError("Simulated failure")

        return Resume.model_validate(VALID_DATA)

    monkeypatch.setattr(
        main,
        "extract_with_retries",
        mock_extract
    )

    results = main.process_documents()

    assert len(results) == 2

    assert results[0]["status"] == "success"
    assert results[1]["status"] == "failed"

    assert (
        output_dir / "resume_01.json"
    ).exists()

    assert not (
        output_dir / "resume_02.json"
    ).exists()


def test_evaluation_comparison():
    expected = Resume.model_validate(VALID_DATA)

    predicted_data = {
        **VALID_DATA,
        "skills": ["Python", "Java"]
    }

    predicted = Resume.model_validate(
        predicted_data
    )

    results = compare_resumes(
        expected, predicted
    )

    assert results["name"] is True
    assert results["skills"] is False
