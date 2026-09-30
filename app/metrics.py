from statistics import mean, median


def calculate_tokens_per_second(
    output_tokens: int | None,
    eval_duration_ns: int | None
) -> float | None:

    if not output_tokens:
        return None

    if not eval_duration_ns:
        return None

    duration_seconds = (
        eval_duration_ns / 1_000_000_000
    )

    if duration_seconds <= 0:
        return None

    return output_tokens / duration_seconds


def calculate_stats(logs: list[dict]) -> dict:

    successful = [
        log
        for log in logs
        if log.get("status") == "success"
    ]

    errors = [
        log
        for log in logs
        if log.get("status") == "error"
    ]

    latencies = [
        log["total_latency_ms"]
        for log in successful
        if log.get("total_latency_ms") is not None
    ]

    ttfts = [
        log["time_to_first_token_ms"]
        for log in successful
        if log.get("time_to_first_token_ms") is not None
    ]

    speeds = [
        log["tokens_per_second"]
        for log in successful
        if log.get("tokens_per_second") is not None
    ]

    return {
        "total_requests": len(logs),

        "successful_requests": len(
            successful
        ),

        "error_requests": len(
            errors
        ),

        "success_rate": (
            len(successful) / len(logs) * 100
            if logs
            else 0
        ),

        "average_latency_ms": (
            mean(latencies)
            if latencies
            else None
        ),

        "median_latency_ms": (
            median(latencies)
            if latencies
            else None
        ),

        "average_ttft_ms": (
            mean(ttfts)
            if ttfts
            else None
        ),

        "average_tokens_per_second": (
            mean(speeds)
            if speeds
            else None
        )
    }