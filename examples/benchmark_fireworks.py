"""Example: Benchmark Fireworks AI on AMD MI300X."""

import requests

# Configuration
BASE_URL = "http://localhost:8000"


def benchmark_fireworks(model="glm-5.2", prompt="Hello, world!", iterations=3):
    """Run Fireworks AI benchmark."""

    response = requests.get(
        f"{BASE_URL}/api/benchmarks/fireworks",
        params={
            "model": model,
            "prompt": prompt,
            "iterations": iterations,
        },
    )

    if response.status_code == 200:
        results = response.json()
        print(f"Model: {results['model']}")
        print(f"Hardware: {results['hardware']}")
        print(f"Average latency: {results['avg_latency_ms']:.2f}ms")
        print(f"Average tokens/sec: {results['avg_tokens_per_second']:.2f}")
        print(f"Total tokens: {results['total_tokens']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    benchmark_fireworks()
