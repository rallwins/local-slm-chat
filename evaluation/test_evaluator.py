import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from evaluation.evaluator import (
    evaluate_case,
    load_dataset,
    score_answer,
    summarize_results,
)


class DatasetTests(unittest.TestCase):
    def test_loads_cases_and_rejects_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            dataset_path = Path(directory) / "cases.jsonl"
            case = {
                "id": "one",
                "question": "What is Spark?",
                "expected_keywords": ["distributed"],
            }
            dataset_path.write_text(
                json.dumps(case) + "\n" + json.dumps(case) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "duplicate id"):
                load_dataset(dataset_path)

    def test_rejects_empty_dataset(self):
        with tempfile.TemporaryDirectory() as directory:
            dataset_path = Path(directory) / "empty.jsonl"
            dataset_path.write_text("\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Dataset is empty"):
                load_dataset(dataset_path)


class ScoringTests(unittest.TestCase):
    def test_keyword_matching_is_case_insensitive_and_word_bounded(self):
        score = score_answer(
            "Spark uses Executors to run tasks. MySQL is unrelated.",
            ["executor", "tasks", "sql"],
        )

        self.assertEqual(score["matched_keywords"], ["executor", "tasks"])
        self.assertEqual(score["missing_keywords"], ["sql"])
        self.assertAlmostEqual(score["keyword_coverage"], 2 / 3)

    def test_summary_ignores_failed_cases_for_quality_average(self):
        summary = summarize_results([
            {
                "prompt_template": "data_engineer:v1",
                "status": "success",
                "keyword_coverage": 0.5,
                "latency_ms": 100,
            },
            {
                "prompt_template": "data_engineer:v1",
                "status": "error",
                "keyword_coverage": None,
                "latency_ms": 10,
            },
        ])

        self.assertEqual(summary["data_engineer:v1"]["errors"], 1)
        self.assertEqual(
            summary["data_engineer:v1"]["mean_keyword_coverage"],
            0.5,
        )


class EvaluationTests(unittest.TestCase):
    def test_evaluates_response_and_captures_ollama_metrics(self):
        async def fake_stream(model, messages):
            self.assertEqual(model, "test-model")
            self.assertEqual(messages[-1]["content"], "Explain Spark.")
            yield {"message": {"content": "Spark uses a driver and executors."}}
            yield {
                "done": True,
                "prompt_eval_count": 12,
                "eval_count": 8,
                "eval_duration": 2_000_000_000,
            }

        case = {
            "id": "spark",
            "question": "Explain Spark.",
            "expected_keywords": ["driver", "executor"],
        }
        result = asyncio.run(evaluate_case(
            case,
            "test-model",
            "data_engineer:v1",
            stream=fake_stream,
        ))

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["keyword_coverage"], 1.0)
        self.assertEqual(result["prompt_tokens"], 12)
        self.assertEqual(result["output_tokens"], 8)
        self.assertEqual(result["tokens_per_second"], 4.0)


if __name__ == "__main__":
    unittest.main()