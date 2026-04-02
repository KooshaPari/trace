"""Version chain and Merkle proof endpoints.

Provides blockchain-style versioning and baseline verification endpoints.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from tracertm.api.deps import auth_guard, get_db
from tracertm.repositories import (
    BaselineRepository,
    SpecEmbeddingRepository,
    VersionBlockRepository,
)
from tracertm.schemas.spec_analytics import (
    ContentAddressResponse,
    MerkleProofResponse,
    VersionChainEntry,
    VersionChainResponse,
)
from tracertm.services import spec_analytics_service

router = APIRouter(prefix="/analytics", tags=["Item Spec Analytics - Versioning"])

version_block_repo = VersionBlockRepository()
baseline_repo = BaselineRepository()
embedding_repo = SpecEmbeddingRepository()


@router.get(
    "/{spec_type}/{spec_id}/version-chain",
    response_model=VersionChainResponse,
)
async def get_version_chain(
    _project_id: Annotated[str, Path(description="Project ID")],
    spec_type: Annotated[
        str, Path(pattern="^(requirements|tests|epics|stories|tasks|defects)$", description="Spec type")
    ],
    spec_id: Annotated[str, Path(description="Spec ID")],
    limit: Annotated[int, Query(ge=1, le=200, description="Max chain entries")] = 50,
    _claims: dict[str, object] = Depends(auth_guard),
    db: AsyncSession = Depends(get_db),
) -> VersionChainResponse:
    """Retrieve the version chain (blockchain-style history) for a specification item."""
    try:
        blocks = await version_block_repo.get_version_chain(db, spec_id, spec_type, limit)
        chain_index = await version_block_repo.get_chain_index(db, spec_id, spec_type)

        entries: list[VersionChainEntry] = [
            VersionChainEntry(
                version_hash=block.content_hash or block.block_id,
                version_number=block.version_number,
                content_hash=block.content_hash,
                previous_hash=block.previous_block_id,
                created_at=block.timestamp,
                created_by=block.author_id,
                change_summary=block.change_summary,
            )
            for block in blocks
        ]

        return VersionChainResponse(
            spec_id=spec_id,
            chain_head=(chain_index.chain_head_id or "") if chain_index else "",
            chain_length=chain_index.chain_length if chain_index else 0,
            entries=entries,
            chain_valid=chain_index.is_valid if chain_index else True,
            broken_links=chain_index.broken_links if chain_index else [],
            generated_at=datetime.now(UTC),
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post(
    "/{spec_type}/{spec_id}/verify-baseline",
    response_model=MerkleProofResponse,
)
async def verify_baseline(
    _project_id: Annotated[str, Path(description="Project ID")],
    _spec_type: Annotated[
        str, Path(pattern="^(requirements|tests|epics|stories|tasks|defects)$", description="Spec type")
    ],
    spec_id: Annotated[str, Path(description="Spec ID")],
    baseline_root: Annotated[str, Query(description="Merkle root to verify against")],
    _claims: Annotated[dict[str, object], Depends(auth_guard)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MerkleProofResponse:
    """Verify a spec item against a baseline Merkle root."""
    try:
        baseline = await baseline_repo.get_baseline_by_root(db, baseline_root)
        if not baseline:
            return MerkleProofResponse(
                spec_id=spec_id,
                root=baseline_root,
                proof=[],
                leaf_index=0,
                leaf_hash="",
                verified=False,
                verification_path=[],
                tree_size=0,
                algorithm="sha256",
                generated_at=datetime.now(UTC),
            )

        proof = await baseline_repo.get_merkle_proof(db, baseline.baseline_id, spec_id)
        if not proof:
            return MerkleProofResponse(
                spec_id=spec_id,
                root=baseline_root,
                proof=[],
                leaf_index=0,
                leaf_hash="",
                verified=False,
                verification_path=[],
                tree_size=0,
                algorithm="sha256",
                generated_at=datetime.now(UTC),
            )

        is_valid = baseline_repo.verify_proof(proof.leaf_hash, proof.proof_path, proof.root_hash)

        return MerkleProofResponse(
            spec_id=spec_id,
            root=proof.root_hash,
            proof=[],
            leaf_index=0,
            leaf_hash=proof.leaf_hash,
            verified=is_valid,
            verification_path=proof.proof_path,
            tree_size=0,
            algorithm="sha256",
            generated_at=proof.computed_at,
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/{spec_type}/{spec_id}/merkle-proof",
    response_model=MerkleProofResponse,
)
async def get_merkle_proof(
    _project_id: Annotated[str, Path(description="Project ID")],
    _spec_type: Annotated[
        str, Path(pattern="^(requirements|tests|epics|stories|tasks|defects)$", description="Spec type")
    ],
    spec_id: Annotated[str, Path(description="Spec ID")],
    baseline_id: Annotated[
        str | None, Query(description="Baseline ID to get proof from (optional, uses latest if not specified)")
    ] = None,
    _claims: dict[str, object] = Depends(auth_guard),
    db: AsyncSession = Depends(get_db),
) -> MerkleProofResponse:
    """Get a Merkle proof for a spec item in a specific baseline."""
    try:
        if baseline_id:
            proof = await baseline_repo.get_merkle_proof(db, baseline_id, spec_id)
            if not proof:
                return MerkleProofResponse(
                    spec_id=spec_id,
                    root="",
                    proof=[],
                    leaf_index=0,
                    leaf_hash="",
                    verified=False,
                    verification_path=[],
                    tree_size=0,
                    algorithm="sha256",
                    generated_at=datetime.now(UTC),
                )

            await baseline_repo.get_baseline(db, baseline_id)

            return MerkleProofResponse(
                spec_id=spec_id,
                root=proof.root_hash,
                proof=[],
                leaf_index=0,
                leaf_hash=proof.leaf_hash,
                verified=proof.verified if proof.verified is not None else False,
                verification_path=proof.proof_path,
                tree_size=0,
                algorithm="sha256",
                generated_at=proof.computed_at,
            )

        return MerkleProofResponse(
            spec_id=spec_id,
            root="",
            proof=[],
            leaf_index=0,
            leaf_hash="",
            verified=False,
            verification_path=[],
            tree_size=0,
            algorithm="sha256",
            generated_at=datetime.now(UTC),
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/{spec_type}/{spec_id}/content-address",
    response_model=ContentAddressResponse,
)
async def get_content_address(
    project_id: Annotated[str, Path(description="Project ID")],
    spec_type: Annotated[
        str, Path(pattern="^(requirements|tests|epics|stories|tasks|defects)$", description="Spec type")
    ],
    spec_id: Annotated[str, Path(description="Spec ID")],
    _claims: Annotated[dict[str, object], Depends(auth_guard)],
    _db: Annotated[AsyncSession, Depends(get_db)],
) -> ContentAddressResponse:
    """Get the content address (CID) for a specification item."""
    try:
        placeholder_content = {"id": spec_id, "type": spec_type, "project_id": project_id}
        content_address = spec_analytics_service.generate_content_address(placeholder_content)
        now = content_address.created_at
        return ContentAddressResponse(
            spec_id=spec_id,
            content_hash=content_address.cid,
            content_cid=content_address.cid,
            created_at=now,
            last_modified_at=now,
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
