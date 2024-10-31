# type: ignore
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fast_graphrag._graphrag import BaseGraphRAG
from fast_graphrag._types import TContext, TQueryResponse


class TestBaseGraphRAG(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.llm_service = AsyncMock()
        self.chunking_service = AsyncMock()
        self.information_extraction_service = MagicMock()
        self.information_extraction_service.extract_entities_from_query = AsyncMock()
        self.state_manager = AsyncMock()

        self.graph_rag = BaseGraphRAG(
            working_dir="test_dir",
            domain="test_domain",
            example_queries="test_query",
            entity_types=["type1", "type2"],
            llm_service=self.llm_service,
            chunking_service=self.chunking_service,
            information_extraction_service=self.information_extraction_service,
            state_manager=self.state_manager,
        )

    async def test_async_insert(self):
        self.chunking_service.extract = AsyncMock(return_value=["chunked_data"])
        self.state_manager.filter_new_chunks = AsyncMock(return_value=["new_chunks"])
        self.information_extraction_service.extract = MagicMock(return_value=["subgraph"])
        self.state_manager.upsert = AsyncMock()

        await self.graph_rag.async_insert("test_content", {"meta": "data"})

        self.chunking_service.extract.assert_called_once()
        self.state_manager.filter_new_chunks.assert_called_once()
        self.information_extraction_service.extract.assert_called_once()
        self.state_manager.upsert.assert_called_once()

    @patch("fast_graphrag._graphrag.format_and_send_prompt", new_callable=AsyncMock)
    async def test_async_query(self, format_and_send_prompt):
        self.information_extraction_service.extract_entities_from_query = AsyncMock(return_value=["entities"])
        self.state_manager.get_context = AsyncMock(return_value=TContext([], [], []))
        format_and_send_prompt.return_value=("response", None)

        response = await self.graph_rag.async_query("test_query")

        self.information_extraction_service.extract_entities_from_query.assert_called_once()
        self.state_manager.get_context.assert_called_once()
        format_and_send_prompt.assert_called_once()
        self.assertIsInstance(response, TQueryResponse)


if __name__ == "__main__":
    unittest.main()
