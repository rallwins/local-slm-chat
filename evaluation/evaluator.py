import json
import re
import time
from pathlib import Path
from statistics import mean
from typing import Any, AsyncIterator, Callable

from app.metrics import calculate_tokens_per_second
from app.ollama import chat_stream
from app.prompts import PROMPT_TEMPLATES


ChatStream = Callable[
	[str, list[dict[str, str]]],
	AsyncIterator[dict[str, Any]]
]


def load_dataset(path: Path) -> list[dict[str, Any]]:
	cases = []
	seen_ids = set()

	with path.open(encoding="utf-8") as dataset_file:
		for line_number, line in enumerate(dataset_file, start=1):
			if not line.strip():
				continue

			try:
				case = json.loads(line)
			except json.JSONDecodeError as exc:
				raise ValueError(
					f"{path}:{line_number}: invalid JSON: {exc.msg}"
				) from exc

			if not isinstance(case, dict):
				raise ValueError(
					f"{path}:{line_number}: each case must be a JSON object"
				)

			case_id = case.get("id")
			question = case.get("question")
			keywords = case.get("expected_keywords")

			if not isinstance(case_id, str) or not case_id.strip():
				raise ValueError(
					f"{path}:{line_number}: id must be a non-empty string"
				)
			if case_id in seen_ids:
				raise ValueError(
					f"{path}:{line_number}: duplicate id {case_id!r}"
				)
			if not isinstance(question, str) or not question.strip():
				raise ValueError(
					f"{path}:{line_number}: question must be a non-empty string"
				)
			if (
				not isinstance(keywords, list)
				or not keywords
				or any(
					not isinstance(keyword, str) or not keyword.strip()
					for keyword in keywords
				)
			):
				raise ValueError(
					f"{path}:{line_number}: expected_keywords must be a non-empty list of strings"
				)

			seen_ids.add(case_id)
			cases.append({
				"id": case_id,
				"question": question,
				"expected_keywords": keywords,
			})

	if not cases:
		raise ValueError(f"Dataset is empty: {path}")

	return cases


def score_answer(
	answer: str,
	expected_keywords: list[str]
) -> dict[str, Any]:
	normalized_answer = " ".join(answer.casefold().split())
	matched = []
	missing = []

	for keyword in expected_keywords:
		normalized_keyword = " ".join(keyword.casefold().split())
		keyword_parts = [
			re.escape(part)
			for part in normalized_keyword.split()
		]
		keyword_parts[-1] += "s?"
		pattern = (
			r"(?<!\w)"
			+ r"\s+".join(keyword_parts)
			+ r"(?!\w)"
		)

		if re.search(pattern, normalized_answer):
			matched.append(keyword)
		else:
			missing.append(keyword)

	return {
		"matched_keywords": matched,
		"missing_keywords": missing,
		"keyword_coverage": len(matched) / len(expected_keywords),
	}


async def evaluate_case(
	case: dict[str, Any],
	model: str,
	prompt_template: str,
	stream: ChatStream = chat_stream,
) -> dict[str, Any]:
	template = PROMPT_TEMPLATES.get(prompt_template)
	if template is None:
		raise ValueError(f"Unknown prompt template: {prompt_template}")

	messages = [
		{"role": "system", "content": template.system_prompt},
		{"role": "user", "content": case["question"]},
	]
	started_at = time.perf_counter()
	answer_parts = []
	final_chunk: dict[str, Any] = {}

	try:
		async for chunk in stream(model, messages):
			message = chunk.get("message", {})
			content = message.get("content", "")
			if isinstance(content, str):
				answer_parts.append(content)
			if chunk.get("done"):
				final_chunk = chunk

		answer = "".join(answer_parts)
		result = {
			"case_id": case["id"],
			"question": case["question"],
			"model": model,
			"prompt_template": prompt_template,
			"status": "success",
			"answer": answer,
			**score_answer(answer, case["expected_keywords"]),
			"prompt_tokens": final_chunk.get("prompt_eval_count"),
			"output_tokens": final_chunk.get("eval_count"),
			"tokens_per_second": calculate_tokens_per_second(
				final_chunk.get("eval_count"),
				final_chunk.get("eval_duration"),
			),
		}
	except Exception as exc:
		result = {
			"case_id": case["id"],
			"question": case["question"],
			"model": model,
			"prompt_template": prompt_template,
			"status": "error",
			"answer": "".join(answer_parts),
			"error": str(exc),
			"keyword_coverage": None,
		}

	result["latency_ms"] = (time.perf_counter() - started_at) * 1000
	return result


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
	summary = {}

	template_ids = dict.fromkeys(
		result["prompt_template"] for result in results
	)
	for template_id in template_ids:
		template_results = [
			result
			for result in results
			if result["prompt_template"] == template_id
		]
		successful = [
			result
			for result in template_results
			if result["status"] == "success"
		]
		coverages = [
			result["keyword_coverage"]
			for result in successful
		]

		summary[template_id] = {
			"cases": len(template_results),
			"errors": len(template_results) - len(successful),
			"mean_keyword_coverage": mean(coverages) if coverages else None,
			"fully_covered_cases": sum(
				coverage == 1.0 for coverage in coverages
			),
			"mean_latency_ms": (
				mean(result["latency_ms"] for result in successful)
				if successful
				else None
			),
		}

	return summary


def write_results(path: Path, results: list[dict[str, Any]]) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	with path.open("w", encoding="utf-8") as results_file:
		for result in results:
			results_file.write(
				json.dumps(result, ensure_ascii=False) + "\n"
			)
