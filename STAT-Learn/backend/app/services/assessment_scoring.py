"""Deterministic mock scoring for adaptive assessments."""

MOCK_ANSWER_KEY: dict[str, str] = {
    "py_q1": "def",
    "py_q2": "list",
    "py_q3": "True",
    "sql_q1": "SELECT",
    "sql_q2": "JOIN",
}


def score_answers(answers: list[dict]) -> float:
    if not answers:
        return 0.0
    correct = 0
    for entry in answers:
        qid = entry.get("question_id")
        ans = str(entry.get("answer", "")).strip()
        expected = MOCK_ANSWER_KEY.get(qid)
        if expected and ans.lower() == expected.lower():
            correct += 1
    return round((correct / len(answers)) * 100.0, 2)
