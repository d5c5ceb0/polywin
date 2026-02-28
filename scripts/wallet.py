#!/usr/bin/env python3
"""Wallet management commands - environment variable mode only."""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts import cli


def run_cli(args: list[str], capture: bool = False) -> tuple[int, str]:
    """Run polymarket CLI and optionally capture output."""
    if not cli.check_installed():
        return 1, "polymarket CLI not installed"
    
    cmd = ["polymarket"]
    
    # Add default signature type if not set
    if not os.environ.get("POLYMARKET_SIGNATURE_TYPE"):
        cmd.extend(["--signature-type", cli.DEFAULT_SIGNATURE_TYPE])
    
    cmd.extend(["-o", "json"] + args)
    
    if capture:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout
    else:
        result = subprocess.run(cmd)
        return result.returncode, ""


def get_private_key() -> str | None:
    """Get private key from environment."""
    return os.environ.get("POLYMARKET_PRIVATE_KEY")


def get_wallet_info() -> dict | None:
    """Get full wallet info including proxy address."""
    if not get_private_key():
        return None
    
    code, output = run_cli(["wallet", "show"], capture=True)
    if code == 0 and output.strip():
        try:
            return json.loads(output)
        except:
            pass
    return None


def get_balance() -> dict:
    """Get wallet balances (from proxy wallet)."""
    result = {"usdc": 0}
    
    code, output = run_cli(["clob", "balance", "--asset-type", "collateral"], capture=True)
    if code == 0:
        try:
            data = json.loads(output)
            result["usdc"] = float(data.get("balance", 0))
        except:
            pass
    
    return result


def check_approvals() -> bool:
    """Check if approvals are set (checks proxy address approvals)."""
    code, output = run_cli(["approve", "check"], capture=True)
    if code == 0:
        try:
            data = json.loads(output)
            # Response is array of contracts, each with ctf_approved and usdc_approved
            if isinstance(data, list):
                return all(
                    item.get("ctf_approved", False) and item.get("usdc_approved", False)
                    for item in data
                )
        except:
            pass
    return False


def cmd_status(args):
    """Show wallet status and balances."""
    pk = get_private_key()
    if not pk:
        print("❌ POLYMARKET_PRIVATE_KEY not set")
        print("   Set the environment variable with your private key")
        return 1
    
    info = get_wallet_info()
    if not info:
        print("❌ Could not get wallet info")
        return 1
    
    eoa_addr = info.get("address")
    proxy_addr = info.get("proxy_address")
    sig_type = info.get("signature_type", "unknown")
    
    print(f"🔑 EOA Address:   {eoa_addr}")
    if proxy_addr:
        print(f"📍 Proxy Address: {proxy_addr}")
    print(f"📝 Signature:     {sig_type}")
    print()
    
    balance = get_balance()
    print(f"💰 USDC.e Balance: ${balance['usdc']:.2f}")
    
    approved = check_approvals()
    status = "✅ Ready" if approved else "⚠️  Not set (run: wallet.py approve)"
    print(f"📋 Approvals:      {status}")
    
    if args.json:
        print(json.dumps({
            "eoa_address": eoa_addr,
            "proxy_address": proxy_addr,
            "signature_type": sig_type,
            "usdc_balance": balance["usdc"],
            "approvals_set": approved,
        }, indent=2))
    
    return 0


def cmd_approve(args):
    """Set contract approvals."""
    if not get_private_key():
        print("❌ POLYMARKET_PRIVATE_KEY not set")
        return 1
    
    if check_approvals() and not args.force:
        print("✅ Approvals already set")
        return 0
    
    print("📝 Setting contract approvals...")
    print("   This requires MATIC for gas fees.")
    print()
    
    code = cli.run(["approve", "set"], json_output=False)
    
    if code == 0:
        print("\n✅ Approvals set! You can now trade.")
    else:
        print("\n❌ Failed to set approvals")
        print("   Make sure you have MATIC for gas")
    
    return code


def cmd_deposit(args):
    """Show deposit information."""
    if not get_private_key():
        print("❌ POLYMARKET_PRIVATE_KEY not set")
        return 1
    
    info = get_wallet_info()
    if not info:
        print("❌ Could not get wallet info")
        return 1
    
    proxy_addr = info.get("proxy_address")
    eoa_addr = info.get("address")
    
    print("💰 Deposit funds to start trading\n")
    
    if proxy_addr:
        print("   ⚠️  IMPORTANT: Send USDC.e to PROXY address!")
        print()
        print(f"   ✅ Proxy Address: {proxy_addr}")
        print(f"   ❌ NOT EOA:       {eoa_addr}")
        print()
        print("   Network: Polygon")
        print()
        print("   Required tokens:")
        print(f"   • USDC.e → send to PROXY: {proxy_addr}")
        print(f"   • MATIC (for gas) → send to EOA: {eoa_addr}")
    else:
        print(f"   Address: {eoa_addr}")
        print("   Network: Polygon")
        print()
        print("   Required tokens:")
        print("   • MATIC (for gas) - 0.1-1 MATIC recommended")
        print("   • USDC.e (for trading)")
    
    print()
    print("   ⚠️  WARNING:")
    print("   • Must be USDC.e, NOT native USDC!")
    print("   • USDC.e contract: 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Wallet management (requires POLYMARKET_PRIVATE_KEY env var)"
    )
    sub = parser.add_subparsers(dest="cmd")
    
    # status
    p = sub.add_parser("status", help="Show wallet status")
    p.add_argument("-j", "--json", action="store_true", help="JSON output")
    
    # approve
    p = sub.add_parser("approve", help="Set contract approvals")
    p.add_argument("-f", "--force", action="store_true", help="Force re-approve")
    
    # deposit
    p = sub.add_parser("deposit", help="Show deposit info")
    
    args = parser.parse_args()
    
    handlers = {
        "status": cmd_status,
        "approve": cmd_approve,
        "deposit": cmd_deposit,
    }
    
    if args.cmd in handlers:
        return handlers[args.cmd](args)
    
    # Default: show status
    if not args.cmd:
        args.json = False
        return cmd_status(args)
    
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
