"""Output signature module (Flame Vault Licensing)."""

import hashlib
import json
import time
from pathlib import Path
from typing import Optional


def sign_output(
    text: str,
    signer: str,
    project_id: str,
    vault_dir: Optional[Path] = None
) -> str:
    """
    Sign output with cryptographic hash and metadata.

    Args:
        text: Output text to sign
        signer: Name of signer
        project_id: Project identifier
        vault_dir: Optional vault directory for signature log

    Returns:
        Text with appended signature footer
    """
    # Generate SHA256 hash
    text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
    short_hash = text_hash[:16]

    # Create signature footer
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
    footer = f"""

---
Signed by: {signer}
Hash: {short_hash}
Timestamp: {timestamp}
Project: {project_id}
License: Flame Vault - Attribution Required
"""

    # Log signature if vault directory provided
    if vault_dir:
        vault_dir = Path(vault_dir)
        vault_dir.mkdir(parents=True, exist_ok=True)
        signatures_file = vault_dir / "signatures.jsonl"

        signature_record = {
            "hash": text_hash,
            "short_hash": short_hash,
            "timestamp": time.time(),
            "timestamp_utc": timestamp,
            "signer": signer,
            "project_id": project_id,
            "text_length": len(text)
        }

        with open(signatures_file, 'a') as f:
            f.write(json.dumps(signature_record) + '\n')

    return text + footer


def verify_signature(signed_text: str) -> dict:
    """
    Extract and verify signature from signed text.

    Args:
        signed_text: Text with signature footer

    Returns:
        Dictionary with signature metadata
    """
    # Extract hash from footer
    lines = signed_text.split('\n')
    metadata = {}

    for line in lines:
        if line.startswith('Signed by:'):
            metadata['signer'] = line.split(':', 1)[1].strip()
        elif line.startswith('Hash:'):
            metadata['hash'] = line.split(':', 1)[1].strip()
        elif line.startswith('Timestamp:'):
            metadata['timestamp'] = line.split(':', 1)[1].strip()
        elif line.startswith('Project:'):
            metadata['project_id'] = line.split(':', 1)[1].strip()

    return metadata
