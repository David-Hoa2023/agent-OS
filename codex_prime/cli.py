"""Command-line interface for Codex Prime."""

import argparse
import sys
from pathlib import Path


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Codex Prime - Agent OS",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--project",
        type=str,
        default="default",
        help="Project ID for state isolation"
    )

    parser.add_argument(
        "--persona",
        type=str,
        help="Path to persona YAML file"
    )

    parser.add_argument(
        "--fortify",
        type=str,
        help="Fortification loops (e.g., x2, x3)"
    )

    parser.add_argument(
        "--resurrect",
        action="store_true",
        help="Resurrect context from previous session"
    )

    parser.add_argument(
        "--signer",
        type=str,
        help="Signer name for output signatures"
    )

    args = parser.parse_args()

    print(f"Codex Prime CLI")
    print(f"Project: {args.project}")

    if args.persona:
        print(f"Persona: {args.persona}")

    if args.resurrect:
        print("Resurrecting context...")

    print("\nType your message (Ctrl+D or Ctrl+Z to submit):")

    # Read from stdin
    try:
        user_input = sys.stdin.read().strip()
        if user_input:
            print(f"\nReceived: {user_input}")
            print("\n[Response placeholder - agent processing not yet implemented]")
    except KeyboardInterrupt:
        print("\n\nExiting...")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
