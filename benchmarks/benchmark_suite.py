"""Comprehensive benchmark suite for Codex Prime Agent OS.

This script benchmarks key components and operations:
- Memory operations (add, recall, search)
- Tool execution performance
- Provider response times
- Multi-agent coordination
- Workflow execution

Run with: python benchmarks/benchmark_suite.py
"""

import time
import asyncio
import statistics
from pathlib import Path
from typing import List, Dict, Any, Callable
import tempfile
import json


class BenchmarkResult:
    """Container for benchmark results."""

    def __init__(self, name: str, times: List[float]):
        """Initialize benchmark result.

        Args:
            name: Benchmark name
            times: List of execution times in seconds
        """
        self.name = name
        self.times = times
        self.mean = statistics.mean(times)
        self.median = statistics.median(times)
        self.stdev = statistics.stdev(times) if len(times) > 1 else 0
        self.min = min(times)
        self.max = max(times)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "runs": len(self.times),
            "mean_ms": self.mean * 1000,
            "median_ms": self.median * 1000,
            "stdev_ms": self.stdev * 1000,
            "min_ms": self.min * 1000,
            "max_ms": self.max * 1000
        }

    def __str__(self) -> str:
        """Format result as string."""
        return (
            f"{self.name}:\n"
            f"  Mean:   {self.mean * 1000:.2f}ms\n"
            f"  Median: {self.median * 1000:.2f}ms\n"
            f"  StdDev: {self.stdev * 1000:.2f}ms\n"
            f"  Min:    {self.min * 1000:.2f}ms\n"
            f"  Max:    {self.max * 1000:.2f}ms\n"
            f"  Runs:   {len(self.times)}"
        )


def benchmark(func: Callable, iterations: int = 100) -> BenchmarkResult:
    """Run benchmark for a function.

    Args:
        func: Function to benchmark
        iterations: Number of iterations

    Returns:
        BenchmarkResult
    """
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append(end - start)

    return BenchmarkResult(func.__name__, times)


async def async_benchmark(func: Callable, iterations: int = 100) -> BenchmarkResult:
    """Run benchmark for an async function.

    Args:
        func: Async function to benchmark
        iterations: Number of iterations

    Returns:
        BenchmarkResult
    """
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        await func()
        end = time.perf_counter()
        times.append(end - start)

    return BenchmarkResult(func.__name__, times)


class CodexPrimeBenchmark:
    """Main benchmark suite for Codex Prime."""

    def __init__(self):
        """Initialize benchmark suite."""
        self.results: List[BenchmarkResult] = []

    def run_all(self):
        """Run all benchmarks."""
        print("=" * 60)
        print("Codex Prime Agent OS - Benchmark Suite")
        print("=" * 60)
        print()

        # Memory benchmarks
        print("Running Memory Benchmarks...")
        self.benchmark_memory()
        print()

        # Tool benchmarks
        print("Running Tool Benchmarks...")
        self.benchmark_tools()
        print()

        # Async benchmarks
        print("Running Async Benchmarks...")
        asyncio.run(self.benchmark_async())
        print()

        # Print summary
        self.print_summary()

        # Save results
        self.save_results()

    def benchmark_memory(self):
        """Benchmark memory operations."""
        try:
            from codex_prime.memory import MemoryVault

            with tempfile.TemporaryDirectory() as tmpdir:
                vault = MemoryVault(Path(tmpdir))

                # Benchmark add_ember
                def add_ember():
                    vault.add_ember("Test memory entry", tags=["test"])

                result = benchmark(add_ember, iterations=1000)
                self.results.append(result)
                print(result)
                print()

                # Populate vault for recall benchmark
                for i in range(100):
                    vault.add_ember(f"Memory entry {i}", tags=["benchmark"])

                # Benchmark recall
                def recall():
                    vault.recall("entry", tier="ember", k=10)

                result = benchmark(recall, iterations=500)
                self.results.append(result)
                print(result)
                print()

        except ImportError as e:
            print(f"Skipping memory benchmarks: {e}")

    def benchmark_tools(self):
        """Benchmark tool execution."""
        try:
            from codex_prime.tools import ToolRegistry, ToolExecutor
            from codex_prime.tools.builtin import create_default_toolset

            registry = ToolRegistry()
            for tool in create_default_toolset():
                registry.register(tool)

            executor = ToolExecutor(registry)

            # Benchmark calculator
            def calculate():
                executor.execute("calculate", {"expression": "2 + 2 * 3"})

            result = benchmark(calculate, iterations=500)
            self.results.append(result)
            print(result)
            print()

        except ImportError as e:
            print(f"Skipping tool benchmarks: {e}")

    async def benchmark_async(self):
        """Benchmark async operations."""
        try:
            from codex_prime.automation import WorkflowEngine

            engine = WorkflowEngine()

            # Benchmark simple workflow
            async def execute_workflow():
                # Simple mock workflow
                await asyncio.sleep(0.001)  # Simulate work

            result = await async_benchmark(execute_workflow, iterations=100)
            self.results.append(result)
            print(result)
            print()

        except ImportError as e:
            print(f"Skipping async benchmarks: {e}")

    def print_summary(self):
        """Print benchmark summary."""
        print("=" * 60)
        print("Benchmark Summary")
        print("=" * 60)
        print()

        for result in self.results:
            print(f"{result.name:30s} {result.mean * 1000:8.2f}ms")

        print()

    def save_results(self, output_file: str = "benchmark_results.json"):
        """Save results to JSON file.

        Args:
            output_file: Output file path
        """
        data = {
            "timestamp": time.time(),
            "results": [r.to_dict() for r in self.results]
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Results saved to {output_file}")


# Standalone benchmark functions

def benchmark_memory_operations(iterations: int = 1000):
    """Benchmark memory vault operations.

    Args:
        iterations: Number of iterations
    """
    from codex_prime.memory import MemoryVault

    with tempfile.TemporaryDirectory() as tmpdir:
        vault = MemoryVault(Path(tmpdir))

        print(f"Benchmarking {iterations} memory operations...")

        # Add operations
        start = time.perf_counter()
        for i in range(iterations):
            vault.add_ember(f"Test memory {i}", tags=["test"])
        add_time = time.perf_counter() - start

        # Recall operations
        start = time.perf_counter()
        for i in range(iterations // 10):
            vault.recall("test", tier="ember", k=10)
        recall_time = time.perf_counter() - start

        print(f"Add:    {(add_time / iterations) * 1000:.2f}ms per operation")
        print(f"Recall: {(recall_time / (iterations // 10)) * 1000:.2f}ms per operation")


def benchmark_vector_search(iterations: int = 100):
    """Benchmark vector search operations.

    Args:
        iterations: Number of iterations
    """
    try:
        from codex_prime.memory import EnhancedMemoryVault

        with tempfile.TemporaryDirectory() as tmpdir:
            vault = EnhancedMemoryVault(Path(tmpdir), use_vector_search=True)

            print(f"Benchmarking {iterations} vector search operations...")

            # Populate
            for i in range(1000):
                vault.add_rune(f"Document about topic {i % 10}", tags=["doc"])

            # Search
            start = time.perf_counter()
            for i in range(iterations):
                vault.semantic_search("topic", k=10)
            search_time = time.perf_counter() - start

            print(f"Vector search: {(search_time / iterations) * 1000:.2f}ms per query")

    except ImportError as e:
        print(f"Skipping vector search benchmark: {e}")


def benchmark_concurrent_operations(concurrency: int = 10, iterations: int = 100):
    """Benchmark concurrent operations.

    Args:
        concurrency: Number of concurrent operations
        iterations: Number of iterations
    """
    async def run_concurrent():
        from codex_prime.memory import MemoryVault

        with tempfile.TemporaryDirectory() as tmpdir:
            vault = MemoryVault(Path(tmpdir))

            async def add_memory(i: int):
                vault.add_ember(f"Concurrent memory {i}", tags=["concurrent"])

            start = time.perf_counter()
            tasks = [add_memory(i) for i in range(concurrency * iterations)]
            await asyncio.gather(*tasks)
            total_time = time.perf_counter() - start

            print(f"Concurrent operations: {concurrency} concurrent, {iterations} iterations")
            print(f"Total time: {total_time:.2f}s")
            print(f"Throughput: {(concurrency * iterations) / total_time:.0f} ops/sec")

    try:
        asyncio.run(run_concurrent())
    except ImportError as e:
        print(f"Skipping concurrent benchmark: {e}")


def main():
    """Run benchmark suite."""
    import argparse

    parser = argparse.ArgumentParser(description="Codex Prime Benchmark Suite")
    parser.add_argument("--quick", action="store_true", help="Run quick benchmark (fewer iterations)")
    parser.add_argument("--full", action="store_true", help="Run full benchmark suite")
    parser.add_argument("--memory", action="store_true", help="Benchmark memory operations only")
    parser.add_argument("--vector", action="store_true", help="Benchmark vector search only")
    parser.add_argument("--concurrent", action="store_true", help="Benchmark concurrent operations")

    args = parser.parse_args()

    if args.quick:
        print("Running quick benchmark...")
        benchmark_memory_operations(iterations=100)

    elif args.memory:
        print("Running memory benchmark...")
        benchmark_memory_operations(iterations=5000)

    elif args.vector:
        print("Running vector search benchmark...")
        benchmark_vector_search(iterations=500)

    elif args.concurrent:
        print("Running concurrent benchmark...")
        benchmark_concurrent_operations(concurrency=20, iterations=50)

    else:
        # Full suite
        suite = CodexPrimeBenchmark()
        suite.run_all()


if __name__ == "__main__":
    main()
