"""Version chain and Merkle tree analytics module."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from itertools import starmap
from typing import Any

from pydantic import BaseModel


class VersionBlock(BaseModel):
    """Immutable version record with cryptographic linking (blockchain-style)."""

    block_id: str
    previous_block_id: str | None
    timestamp: datetime
    author_id: str
    change_type: str
    change_summary: str
    content_hash: str
    merkle_root: str | None = None
    signature: str | None = None
    nonce: int | None = None


class MerkleProof(BaseModel):
    """Merkle proof for verifying item inclusion in a baseline."""

    leaf_hash: str
    proof_path: list[tuple[str, str]]
    root_hash: str
    item_id: str
    baseline_id: str


class ContentAddress(BaseModel):
    """IPFS-style content identifier."""

    cid: str
    algorithm: str = "sha256"
    size_bytes: int
    content_type: str
    created_at: datetime


class VersionChain:
    """Blockchain-style cryptographic version chain."""

    @staticmethod
    def create_genesis_block(
        content: dict[str, Any],
        author_id: str,
        change_summary: str = "Initial creation",
    ) -> VersionBlock:
        """Create the first block in a version chain."""
        content_hash = VersionChain._hash_content(content)
        timestamp = datetime.now(UTC)
        block_data = {
            "previous_block_id": None,
            "timestamp": timestamp.isoformat(),
            "author_id": author_id,
            "change_type": "created",
            "change_summary": change_summary,
            "content_hash": content_hash,
        }
        block_id = VersionChain._hash_block(block_data)
        return VersionBlock(
            block_id=block_id,
            previous_block_id=None,
            timestamp=timestamp,
            author_id=author_id,
            change_type="created",
            change_summary=change_summary,
            content_hash=content_hash,
        )

    @staticmethod
    def add_block(
        previous_block: VersionBlock,
        content: dict[str, Any],
        author_id: str,
        change_type: str,
        change_summary: str,
    ) -> VersionBlock:
        """Add a new block linked to previous."""
        content_hash = VersionChain._hash_content(content)
        timestamp = datetime.now(UTC)
        block_data = {
            "previous_block_id": previous_block.block_id,
            "timestamp": timestamp.isoformat(),
            "author_id": author_id,
            "change_type": change_type,
            "change_summary": change_summary,
            "content_hash": content_hash,
        }
        block_id = VersionChain._hash_block(block_data)
        return VersionBlock(
            block_id=block_id,
            previous_block_id=previous_block.block_id,
            timestamp=timestamp,
            author_id=author_id,
            change_type=change_type,
            change_summary=change_summary,
            content_hash=content_hash,
        )

    @staticmethod
    def verify_chain(blocks: list[VersionBlock]) -> tuple[bool, list[str]]:
        """Verify integrity of the entire version chain."""
        if not blocks:
            return True, []
        issues = []
        if blocks[0].previous_block_id is not None:
            issues.append("Genesis block has non-null previous_block_id")
        for i in range(1, len(blocks)):
            current = blocks[i]
            previous = blocks[i - 1]
            if current.previous_block_id != previous.block_id:
                issues.append(f"Block {i}: previous_block_id mismatch (expected {previous.block_id[:16]}...)")
            if current.timestamp < previous.timestamp:
                issues.append(f"Block {i}: timestamp before previous block")
        return len(issues) == 0, issues

    @staticmethod
    def _hash_content(content: dict[str, Any]) -> str:
        """SHA-256 hash of content."""
        content_str = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(content_str.encode()).hexdigest()

    @staticmethod
    def _hash_block(block_data: dict[str, Any]) -> str:
        """SHA-256 hash of block data."""
        block_str = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_str.encode()).hexdigest()


class MerkleTree:
    """Merkle tree for efficient baseline verification."""

    def __init__(self, items: list[tuple[str, str]]) -> None:
        """Initialize Merkle tree from items."""
        self.items = items
        self.leaves = list(starmap(self._hash_leaf, items))
        self.tree = self._build_tree(self.leaves.copy())
        self.root = self.tree[-1][0] if self.tree else ""

    def get_proof(self, item_id: str) -> MerkleProof | None:
        """Generate inclusion proof for an item."""
        leaf_index = None
        for i, (iid, _) in enumerate(self.items):
            if iid == item_id:
                leaf_index = i
                break
        if leaf_index is None:
            return None
        proof_path = []
        index = leaf_index
        level_size = len(self.leaves)
        for level in range(len(self.tree) - 1):
            sibling_index = index ^ 1
            if sibling_index < level_size:
                sibling_hash = self.tree[level][sibling_index]
                direction = "right" if index % 2 == 0 else "left"
                proof_path.append((sibling_hash, direction))
            index //= 2
            level_size = (level_size + 1) // 2
        return MerkleProof(
            leaf_hash=self.leaves[leaf_index],
            proof_path=proof_path,
            root_hash=self.root,
            item_id=item_id,
            baseline_id="",
        )

    @staticmethod
    def verify_proof(proof: MerkleProof) -> bool:
        """Verify a Merkle inclusion proof."""
        current_hash = proof.leaf_hash
        for sibling_hash, direction in proof.proof_path:
            if direction == "left":
                current_hash = MerkleTree._hash_pair(sibling_hash, current_hash)
            else:
                current_hash = MerkleTree._hash_pair(current_hash, sibling_hash)
        return current_hash == proof.root_hash

    def _build_tree(self, leaves: list[str]) -> list[list[str]]:
        """Build complete Merkle tree from leaves."""
        if not leaves:
            return []
        tree = [leaves]
        while len(tree[-1]) > 1:
            level = tree[-1]
            next_level = []
            for i in range(0, len(level), 2):
                if i + 1 < len(level):
                    next_level.append(self._hash_pair(level[i], level[i + 1]))
                else:
                    next_level.append(level[i])
            tree.append(next_level)
        return tree

    @staticmethod
    def _hash_leaf(item_id: str, content_hash: str) -> str:
        """Hash a leaf node."""
        data = f"leaf:{item_id}:{content_hash}"
        return hashlib.sha256(data.encode()).hexdigest()

    @staticmethod
    def _hash_pair(left: str, right: str) -> str:
        """Hash two nodes together."""
        data = f"node:{left}:{right}"
        return hashlib.sha256(data.encode()).hexdigest()


__all__ = [
    "ContentAddress",
    "MerkleProof",
    "MerkleTree",
    "VersionBlock",
    "VersionChain",
]
