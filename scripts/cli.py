"""CLI utilities for polymarket skill."""

import os
import subprocess
import shutil
import json

# Default signature type
DEFAULT_SIGNATURE_TYPE = "gnosis-safe"


def check_installed() -> bool:
    """Check if polymarket CLI is installed."""
    return shutil.which("polymarket") is not None


def check_private_key() -> bool:
    """Check if POLYMARKET_PRIVATE_KEY is set."""
    return bool(os.environ.get("POLYMARKET_PRIVATE_KEY"))


def run(args: list[str], json_output: bool = True) -> int:
    """Run polymarket CLI with arguments.
    
    Args:
        args: Command arguments to pass to polymarket
        json_output: If True, add -o json flag for machine-readable output
    
    Returns:
        Exit code from the command
    """
    if not check_installed():
        error = {
            "error": "polymarket CLI not installed",
            "install": [
                "brew tap Polymarket/polymarket-cli https://github.com/Polymarket/polymarket-cli && brew install polymarket",
                "curl -sSL https://raw.githubusercontent.com/Polymarket/polymarket-cli/main/install.sh | sh"
            ]
        }
        print(json.dumps(error, indent=2))
        return 1
    
    cmd = ["polymarket"]
    
    # Add signature type if not already specified and not set via env
    if "--signature-type" not in args and not os.environ.get("POLYMARKET_SIGNATURE_TYPE"):
        cmd.extend(["--signature-type", DEFAULT_SIGNATURE_TYPE])
    
    if json_output:
        cmd.extend(["-o", "json"])
    cmd.extend(args)
    
    result = subprocess.run(cmd)
    return result.returncode


def get_version() -> str:
    """Get polymarket CLI version."""
    result = subprocess.run(["polymarket", "--version"], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    return "unknown"
