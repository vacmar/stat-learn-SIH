"""Replay the screening answers through the same assessment API the UI uses."""

import json
import urllib.request

from app.data.diagnostic_seed import QUESTIONS, SCREENING_ANSWER_INDEX

BASE = "http://127.0.0.1:8000"
HEADERS = {
    "Content-Type": "application/json",
    "X-Statlearn-Demo-Learner": "arun-kumar",
}


def call(method: str, path: str, body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(BASE + path, data=data, headers=HEADERS, method=method)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def main() -> None:
    created = call("POST", "/assessments/attempts")
    attempt_id = created["attempt_id"]
    for question in QUESTIONS:
        index = SCREENING_ANSWER_INDEX.get(question.id, 0)
        call(
            "POST",
            f"/assessments/attempts/{attempt_id}/answers",
            {"question_id": question.id, "selected_answer": question.options[index]},
        )
    result = call("POST", f"/assessments/attempts/{attempt_id}/complete")
    print(f"attempt {attempt_id}")
    print(f"overall {result['overall_score_percent']}")
    for row in result["competencies"]:
        print(
            f"{row['name']}: {row['score_percent']}% {row['current_level']} -> {row['target_level']} "
            f"gap {row['gap']} {row['status']}"
        )


if __name__ == "__main__":
    main()
