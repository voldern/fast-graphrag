import asyncio
from dataclasses import dataclass, field
from typing import Dict, Generic, Iterable, List, Optional, Type

from scipy.sparse import csr_matrix

from fast_graphrag._llm import BaseEmbeddingService, BaseLLMService
from fast_graphrag._policies._base import (
    BaseEdgeUpsertPolicy,
    BaseGraphUpsertPolicy,
    BaseNodeUpsertPolicy,
    BaseRankingPolicy,
)
from fast_graphrag._storage import (
    BaseBlobStorage,
    BaseGraphStorage,
    BaseIndexedKeyValueStorage,
    BaseVectorStorage,
    Namespace,
)
from fast_graphrag._types import (
    GTChunk,
    GTEdge,
    GTEmbedding,
    GTHash,
    GTId,
    GTNode,
    TContext,
    TDocument,
    TEntity,
    TIndex,
)


@dataclass
class BaseChunkingService(Generic[GTChunk]):
    """Base class for chunk extractor."""

    def __post__init__(self):
        pass

    async def extract(self, data: Iterable[TDocument]) -> Iterable[Iterable[GTChunk]]:
        """Extract unique chunks from the given data."""
        raise NotImplementedError


@dataclass
class BaseInformationExtractionService(Generic[GTChunk, GTNode, GTEdge, GTId]):
    """Base class for entity and relationship extractors."""

    graph_upsert: BaseGraphUpsertPolicy[GTNode, GTEdge, GTId]
    max_gleaning_steps: int = 0

    def extract(
        self, llm: BaseLLMService, documents: Iterable[Iterable[GTChunk]], prompt_kwargs: Dict[str, str]
    ) -> List[asyncio.Future[Optional[BaseGraphStorage[GTNode, GTEdge, GTId]]]]:
        """Extract both entities and relationships from the given data."""
        raise NotImplementedError

    async def extract_entities_from_query(
        self, llm: BaseLLMService, query: str, prompt_kwargs: Dict[str, str]
    ) -> Iterable[TEntity]:
        """Extract entities from the given query."""
        raise NotImplementedError


@dataclass
class BaseStateManagerService(Generic[GTNode, GTEdge, GTHash, GTChunk, GTId, GTEmbedding]):
    """A class for managing state operations."""

    _namespace: Namespace = field(init=False)
    working_dir: str = field()

    graph_storage: BaseGraphStorage[GTNode, GTEdge, GTId] = field()
    entity_storage: BaseVectorStorage[TIndex, GTEmbedding] = field()
    chunk_storage: BaseIndexedKeyValueStorage[GTHash, GTChunk] = field()

    embedding_service: BaseEmbeddingService = field()

    entity_ranking_policy: BaseRankingPolicy = field(default_factory=lambda: BaseRankingPolicy(None))
    relation_ranking_policy: BaseRankingPolicy = field(default_factory=lambda: BaseRankingPolicy(None))
    chunk_ranking_policy: BaseRankingPolicy = field(default_factory=lambda: BaseRankingPolicy(None))

    node_upsert_policy: BaseNodeUpsertPolicy[GTNode, GTId] = field(default_factory=lambda: BaseNodeUpsertPolicy(None))
    edge_upsert_policy: BaseEdgeUpsertPolicy[GTEdge, GTId] = field(default_factory=lambda: BaseEdgeUpsertPolicy(None))

    node_specificity: bool = field(default=False)

    blob_storage_cls: Type[BaseBlobStorage[csr_matrix]] = field(default=BaseBlobStorage)

    async def insert_start(self) -> None:
        """Prepare the storage for indexing before adding new data."""
        raise NotImplementedError

    async def insert_done(self) -> None:
        """Commit the storage operations after indexing."""
        raise NotImplementedError

    async def query_start(self) -> None:
        """Prepare the storage for indexing before adding new data."""
        raise NotImplementedError

    async def query_done(self) -> None:
        """Commit the storage operations after indexing."""
        raise NotImplementedError

    async def filter_new_chunks(self, chunks_per_data: Iterable[Iterable[GTChunk]]) -> List[List[GTChunk]]:
        """Filter the chunks to check for duplicates.

        This method takes a sequence of chunks and returns a sequence of new chunks
        that are not already present in the storage. It uses a hashing mechanism to
        efficiently identify duplicates.

        Args:
            chunks_per_data (Iterable[Iterable[TChunk]]): A sequence of chunks to be filtered.

        Returns:
            Iterable[Iterable[TChunk]]: A sequence of chunks that are not in the storage.
        """
        raise NotImplementedError

    async def upsert(
        self,
        llm: BaseLLMService,
        subgraphs: List[asyncio.Future[Optional[BaseGraphStorage[GTNode, GTEdge, GTId]]]],
        documents: Iterable[Iterable[GTChunk]],
    ) -> None:
        """Clean and upsert entities, relationships, and chunks into the storage."""
        raise NotImplementedError

    async def get_context(
        self, entities: Iterable[TEntity]
    ) -> Optional[TContext[GTNode, GTEdge, GTHash, GTChunk]]:
        """Retrieve relevant state from the storage."""
        raise NotImplementedError
