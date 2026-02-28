#!/usr/bin/env python3
"""On-chain data commands."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts import cli


def main():
    """Run data subcommand."""
    return cli.run(["data"] + sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
