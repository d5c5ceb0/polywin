#!/usr/bin/env python3
"""CLOB (order book) commands."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts import cli


def main():
    """Run clob subcommand."""
    return cli.run(["clob"] + sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
