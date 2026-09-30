import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.prompts import PROMPT_TEMPLATES
from evaluation.evaluator import (
	evaluate_case,
	load_dataset,
	summarize_results,
	write_results,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = Path(__file__).parent / "datasets" / "data_engineering.jsonl"


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Compare prompt templates on a JSONL evaluation dataset."
	)
	parser.add_argument(
		"--model",
		required=True,
		help="Installed Ollama model name, for example llama3.2.",
	)
	parser.add_argument(
		"--dataset",
		type=Path,
		default=DEFAULT_DATASET,
		help=f"JSONL dataset path (default: {DEFAULT_DATASET}).",
	)
	parser.add_argument(
		"--templates",
		nargs="+",
		choices=sorted(PROMPT_TEMPLATES),
		default=list(PROMPT_TEMPLATES),
		help="Prompt template IDs to compare (default: all).",
	)
	parser.add_argument(
		"--output",
		type=Path,
		help="Result JSONL path (default: a timestamped file under evaluation/results).",
	)
	return parser.parse_args()


async def run(args: argparse.Namespace) -> int:
	cases = load_dataset(args.dataset)
	results = []

	for template_id in args.templates:
		for index, case in enumerate(cases, start=1):
			result = await evaluate_case(
				case,
				args.model,
				template_id,
			)
			results.append(result)
			if result["status"] == "error":
				print(
					f"[{template_id}] {case['id']}: ERROR {result['error']}",
					file=sys.stderr,
				)
			else:
				print(
					f"[{template_id}] {index}/{len(cases)} {case['id']}: "
					f"{result['keyword_coverage']:.0%} keyword coverage"
				)

	output_path = args.output
	if output_path is None:
		timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
		output_path = PROJECT_ROOT / "evaluation" / "results" / f"{timestamp}.jsonl"

	write_results(output_path, results)
	print(f"Results: {output_path}")
	print(json.dumps(summarize_results(results), indent=2))

	return int(any(result["status"] == "error" for result in results))


def main() -> int:
	args = parse_args()
	try:
		return asyncio.run(run(args))
	except (OSError, ValueError) as exc:
		print(f"Evaluation failed: {exc}", file=sys.stderr)
		return 2


if __name__ == "__main__":
	raise SystemExit(main())
