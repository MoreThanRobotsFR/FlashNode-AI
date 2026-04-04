import os
import hashlib
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class VaultManager:
    def __init__(self, vault_path: str = None):
        if vault_path is None:
            # Default to project_root/vault
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            vault_path = os.environ.get("VAULT_PATH", os.path.join(base_dir, "vault"))
        
        self.vault_path = vault_path
        self._init_vault()

    def _init_vault(self):
        os.makedirs(self.vault_path, exist_ok=True)
        os.makedirs(os.path.join(self.vault_path, "RP2040"), exist_ok=True)
        os.makedirs(os.path.join(self.vault_path, "ESP32"), exist_ok=True)
        logger.info(f"VaultManager initialized at {self.vault_path}")

    def _calculate_checksum(self, filepath: str, algorithm: str = 'md5') -> str:
        """Calculates the checksum of a file."""
        if not os.path.exists(filepath):
            return None
        
        hash_algo = getattr(hashlib, algorithm)()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_algo.update(chunk)
        return hash_algo.hexdigest()

    def save_firmware(self, target: str, filename: str, content: bytes) -> Dict[str, str]:
        """Saves firmware and generates md5 and sha256 checksums."""
        target_dir = os.path.join(self.vault_path, target.upper())
        if not os.path.exists(target_dir):
            raise ValueError(f"Invalid target: {target}. Must be RP2040 or ESP32")

        filepath = os.path.join(target_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(content)

        # Generate checksums
        md5_hash = self._calculate_checksum(filepath, 'md5')
        sha256_hash = self._calculate_checksum(filepath, 'sha256')

        with open(f"{filepath}.md5", "w") as f:
            f.write(md5_hash)
            
        with open(f"{filepath}.sha256", "w") as f:
            f.write(sha256_hash)
            
        logger.info(f"Saved firmware {filename} to {target_dir}")
        return {"md5": md5_hash, "sha256": sha256_hash}

    def list_firmwares(self) -> Dict[str, List[Dict]]:
        """Lists all firmwares and their details."""
        result = {"RP2040": [], "ESP32": []}
        
        for target in ["RP2040", "ESP32"]:
            target_dir = os.path.join(self.vault_path, target)
            if not os.path.exists(target_dir):
                continue
                
            for filename in os.listdir(target_dir):
                if filename.endswith(".md5") or filename.endswith(".sha256"):
                    continue
                    
                filepath = os.path.join(target_dir, filename)
                size = os.path.getsize(filepath)
                
                # Check for cached checksums
                md5 = None
                if os.path.exists(f"{filepath}.md5"):
                    with open(f"{filepath}.md5", "r") as f:
                        md5 = f.read().strip()
                else:
                    md5 = self._calculate_checksum(filepath, 'md5')

                result[target].append({
                    "filename": filename,
                    "target": target,
                    "size_bytes": size,
                    "md5": md5
                })
                
        return result
        
    def get_firmware_path(self, target: str, filename: str) -> Optional[str]:
        target_dir = os.path.join(self.vault_path, target.upper())
        filepath = os.path.join(target_dir, filename)
        if os.path.exists(filepath):
            return filepath
        return None

vault_manager = VaultManager()
