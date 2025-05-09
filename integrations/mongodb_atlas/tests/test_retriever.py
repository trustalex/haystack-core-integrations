# SPDX-FileCopyrightText: 2023-present deepset GmbH <info@deepset.ai>
#
# SPDX-License-Identifier: Apache-2.0
from unittest.mock import MagicMock, Mock, patch

import pytest
from haystack.dataclasses import Document
from haystack.document_stores.types import FilterPolicy
from haystack.utils.auth import EnvVarSecret

from haystack_integrations.components.retrievers.mongodb_atlas import (
    MongoDBAtlasEmbeddingRetriever,
    MongoDBAtlasFullTextRetriever,
)
from haystack_integrations.document_stores.mongodb_atlas import MongoDBAtlasDocumentStore


class TestEmbeddingRetriever:
    @pytest.fixture
    def mock_client(self):
        with patch(
            "haystack_integrations.document_stores.mongodb_atlas.document_store.MongoClient"
        ) as mock_mongo_client:
            mock_connection = MagicMock()
            mock_database = MagicMock()
            mock_collection_names = MagicMock(return_value=["test_embeddings_collection"])
            mock_database.list_collection_names = mock_collection_names
            mock_connection.__getitem__.return_value = mock_database
            mock_mongo_client.return_value = mock_connection
            yield mock_mongo_client

    def test_init_default(self):
        mock_store = Mock(spec=MongoDBAtlasDocumentStore)
        retriever = MongoDBAtlasEmbeddingRetriever(document_store=mock_store)
        assert retriever.document_store == mock_store
        assert retriever.filters == {}
        assert retriever.top_k == 10
        assert retriever.filter_policy == FilterPolicy.REPLACE

        retriever = MongoDBAtlasEmbeddingRetriever(document_store=mock_store, filter_policy="merge")
        assert retriever.filter_policy == FilterPolicy.MERGE

        with pytest.raises(ValueError):
            MongoDBAtlasEmbeddingRetriever(document_store=mock_store, filter_policy="wrong_policy")

    def test_init(self):
        mock_store = Mock(spec=MongoDBAtlasDocumentStore)
        retriever = MongoDBAtlasEmbeddingRetriever(
            document_store=mock_store,
            filters={"field": "meta.some_field", "operator": "==", "value": "SomeValue"},
            top_k=5,
        )
        assert retriever.document_store == mock_store
        assert retriever.filters == {"field": "meta.some_field", "operator": "==", "value": "SomeValue"}
        assert retriever.top_k == 5
        assert retriever.filter_policy == FilterPolicy.REPLACE

    def test_init_filter_policy_merge(self):
        mock_store = Mock(spec=MongoDBAtlasDocumentStore)
        retriever = MongoDBAtlasEmbeddingRetriever(
            document_store=mock_store,
            filters={"field": "meta.some_field", "operator": "==", "value": "SomeValue"},
            top_k=5,
            filter_policy=FilterPolicy.MERGE,
        )
        assert retriever.document_store == mock_store
        assert retriever.filters == {"field": "meta.some_field", "operator": "==", "value": "SomeValue"}
        assert retriever.top_k == 5
        assert retriever.filter_policy == FilterPolicy.MERGE

    def test_to_dict(self, mock_client, monkeypatch):  # noqa: ARG002  mock_client appears unused but is required
        monkeypatch.setenv("MONGO_CONNECTION_STRING", "test_conn_str")

        document_store = MongoDBAtlasDocumentStore(
            database_name="haystack_integration_test",
            collection_name="test_embeddings_collection",
            vector_search_index="cosine_index",
            full_text_search_index="full_text_index",
        )

        retriever = MongoDBAtlasEmbeddingRetriever(document_store=document_store, filters={"field": "value"}, top_k=5)
        res = retriever.to_dict()
        assert res == {
            "type": "haystack_integrations.components.retrievers.mongodb_atlas.embedding_retriever.MongoDBAtlasEmbeddingRetriever",  # noqa: E501
            "init_parameters": {
                "document_store": {
                    "type": "haystack_integrations.document_stores.mongodb_atlas.document_store.MongoDBAtlasDocumentStore",  # noqa: E501
                    "init_parameters": {
                        "mongo_connection_string": {
                            "env_vars": ["MONGO_CONNECTION_STRING"],
                            "strict": True,
                            "type": "env_var",
                        },
                        "database_name": "haystack_integration_test",
                        "collection_name": "test_embeddings_collection",
                        "vector_search_index": "cosine_index",
                        "full_text_search_index": "full_text_index",
                    },
                },
                "filters": {"field": "value"},
                "top_k": 5,
                "filter_policy": "replace",
            },
        }

    def test_from_dict(self, mock_client, monkeypatch):  # noqa: ARG002  mock_client appears unused but is required
        monkeypatch.setenv("MONGO_CONNECTION_STRING", "test_conn_str")

        data = {
            "type": "haystack_integrations.components.retrievers.mongodb_atlas.embedding_retriever.MongoDBAtlasEmbeddingRetriever",  # noqa: E501
            "init_parameters": {
                "document_store": {
                    "type": "haystack_integrations.document_stores.mongodb_atlas.document_store.MongoDBAtlasDocumentStore",  # noqa: E501
                    "init_parameters": {
                        "mongo_connection_string": {
                            "env_vars": ["MONGO_CONNECTION_STRING"],
                            "strict": True,
                            "type": "env_var",
                        },
                        "database_name": "haystack_integration_test",
                        "collection_name": "test_embeddings_collection",
                        "vector_search_index": "cosine_index",
                        "full_text_search_index": "full_text_index",
                    },
                },
                "filters": {"field": "value"},
                "top_k": 5,
                "filter_policy": "replace",
            },
        }

        retriever = MongoDBAtlasEmbeddingRetriever.from_dict(data)
        document_store = retriever.document_store

        assert isinstance(document_store, MongoDBAtlasDocumentStore)
        assert isinstance(document_store.mongo_connection_string, EnvVarSecret)
        assert document_store.database_name == "haystack_integration_test"
        assert document_store.collection_name == "test_embeddings_collection"
        assert document_store.vector_search_index == "cosine_index"
        assert document_store.full_text_search_index == "full_text_index"
        assert retriever.filters == {"field": "value"}
        assert retriever.top_k == 5
        assert retriever.filter_policy == FilterPolicy.REPLACE

    def test_from_dict_no_filter_policy(self, monkeypatch):  # mock_client appears unused but is required
        monkeypatch.setenv("MONGO_CONNECTION_STRING", "test_conn_str")

        data = {
            "type": "haystack_integrations.components.retrievers.mongodb_atlas.embedding_retriever.MongoDBAtlasEmbeddingRetriever",  # noqa: E501
            "init_parameters": {
                "document_store": {
                    "type": "haystack_integrations.document_stores.mongodb_atlas.document_store.MongoDBAtlasDocumentStore",  # noqa: E501
                    "init_parameters": {
                        "mongo_connection_string": {
                            "env_vars": ["MONGO_CONNECTION_STRING"],
                            "strict": True,
                            "type": "env_var",
                        },
                        "database_name": "haystack_integration_test",
                        "collection_name": "test_embeddings_collection",
                        "vector_search_index": "cosine_index",
                        "full_text_search_index": "full_text_index",
                    },
                },
                "filters": {"field": "value"},
                "top_k": 5,
            },
        }

        retriever = MongoDBAtlasEmbeddingRetriever.from_dict(data)
        document_store = retriever.document_store

        assert isinstance(document_store, MongoDBAtlasDocumentStore)
        assert isinstance(document_store.mongo_connection_string, EnvVarSecret)
        assert document_store.database_name == "haystack_integration_test"
        assert document_store.collection_name == "test_embeddings_collection"
        assert document_store.vector_search_index == "cosine_index"
        assert document_store.full_text_search_index == "full_text_index"
        assert retriever.filters == {"field": "value"}
        assert retriever.top_k == 5
        assert retriever.filter_policy == FilterPolicy.REPLACE  # defaults to REPLACE

    def test_run(self):
        mock_store = Mock(spec=MongoDBAtlasDocumentStore)
        doc = Document(content="Test doc", embedding=[0.1, 0.2])
        mock_store._embedding_retrieval.return_value = [doc]

        retriever = MongoDBAtlasEmbeddingRetriever(document_store=mock_store)
        res = retriever.run(query_embedding=[0.3, 0.5])

        mock_store._embedding_retrieval.assert_called_once_with(query_embedding=[0.3, 0.5], filters={}, top_k=10)

        assert res == {"documents": [doc]}

    def test_run_merge_policy_filter(self):
        mock_store = Mock(spec=MongoDBAtlasDocumentStore)
        doc = Document(content="Test doc", embedding=[0.1, 0.2])
        mock_store._embedding_retrieval.return_value = [doc]

        retriever = MongoDBAtlasEmbeddingRetriever(
            document_store=mock_store,
            filters={"field": "meta.some_field", "operator": "==", "value": "SomeValue"},
            filter_policy=FilterPolicy.MERGE,
        )
        res = retriever.run(
            query_embedding=[0.3, 0.5], filters={"field": "meta.some_field", "operator": "==", "value": "Test"}
        )
        # as the both init and run filters are filtering the same field, the run filter takes precedence
        mock_store._embedding_retrieval.assert_called_once_with(
            query_embedding=[0.3, 0.5],
            filters={"field": "meta.some_field", "operator": "==", "value": "Test"},
            top_k=10,
        )

        assert res == {"documents": [doc]}

    @pytest.mark.asyncio
    async def test_run_async(self):
        mock_store = Mock(spec=MongoDBAtlasDocumentStore)
        doc = Document(content="Test doc", embedding=[0.1, 0.2])
        mock_store._embedding_retrieval_async.return_value = [doc]

        retriever = MongoDBAtlasEmbeddingRetriever(document_store=mock_store)
        res = await retriever.run_async(query_embedding=[0.3, 0.5])

        mock_store._embedding_retrieval_async.assert_called_once_with(query_embedding=[0.3, 0.5], filters={}, top_k=10)

        assert res == {"documents": [doc]}

    @pytest.mark.asyncio
    async def test_run_merge_policy_filter_async(self):
        mock_store = Mock(spec=MongoDBAtlasDocumentStore)
        doc = Document(content="Test doc", embedding=[0.1, 0.2])
        mock_store._embedding_retrieval_async.return_value = [doc]

        retriever = MongoDBAtlasEmbeddingRetriever(
            document_store=mock_store,
            filters={"field": "meta.some_field", "operator": "==", "value": "SomeValue"},
            filter_policy=FilterPolicy.MERGE,
        )
        res = await retriever.run_async(
            query_embedding=[0.3, 0.5], filters={"field": "meta.some_field", "operator": "==", "value": "Test"}
        )
        # as the both init and run filters are filtering the same field, the run filter takes precedence
        mock_store._embedding_retrieval_async.assert_called_once_with(
            query_embedding=[0.3, 0.5],
            filters={"field": "meta.some_field", "operator": "==", "value": "Test"},
            top_k=10,
        )

        assert res == {"documents": [doc]}


class TestFullTextRetriever:
    @pytest.fixture
    def mock_client(self):
        with patch(
            "haystack_integrations.document_stores.mongodb_atlas.document_store.MongoClient"
        ) as mock_mongo_client:
            mock_connection = MagicMock()
            mock_database = MagicMock()
            mock_collection_names = MagicMock(return_value=["test_full_text_collection"])
            mock_database.list_collection_names = mock_collection_names
            mock_connection.__getitem__.return_value = mock_database
            mock_mongo_client.return_value = mock_connection
            yield mock_mongo_client

    def test_init_default(self):
        mock_store = Mock(spec=MongoDBAtlasDocumentStore)
        retriever = MongoDBAtlasFullTextRetriever(document_store=mock_store)
        assert retriever.document_store == mock_store
        assert retriever.filters == {}
        assert retriever.top_k == 10
        assert retriever.filter_policy == FilterPolicy.REPLACE

        retriever = MongoDBAtlasFullTextRetriever(document_store=mock_store, filter_policy="merge")
        assert retriever.filter_policy == FilterPolicy.MERGE

        with pytest.raises(ValueError):
            MongoDBAtlasFullTextRetriever(document_store=mock_store, filter_policy="wrong_policy")

    def test_init(self):
        mock_store = Mock(spec=MongoDBAtlasDocumentStore)
        retriever = MongoDBAtlasFullTextRetriever(
            document_store=mock_store,
            filters={"field": "meta.some_field", "operator": "==", "value": "SomeValue"},
            top_k=5,
        )
        assert retriever.document_store == mock_store
        assert retriever.filters == {"field": "meta.some_field", "operator": "==", "value": "SomeValue"}
        assert retriever.top_k == 5
        assert retriever.filter_policy == FilterPolicy.REPLACE

    def test_init_filter_policy_merge(self):
        mock_store = Mock(spec=MongoDBAtlasDocumentStore)
        retriever = MongoDBAtlasFullTextRetriever(
            document_store=mock_store,
            filters={"field": "meta.some_field", "operator": "==", "value": "SomeValue"},
            top_k=5,
            filter_policy=FilterPolicy.MERGE,
        )
        assert retriever.document_store == mock_store
        assert retriever.filters == {"field": "meta.some_field", "operator": "==", "value": "SomeValue"}
        assert retriever.top_k == 5
        assert retriever.filter_policy == FilterPolicy.MERGE

    def test_to_dict(self, mock_client, monkeypatch):  # noqa: ARG002  mock_client appears unused but is required
        monkeypatch.setenv("MONGO_CONNECTION_STRING", "test_conn_str")

        document_store = MongoDBAtlasDocumentStore(
            database_name="haystack_integration_test",
            collection_name="test_full_text_collection",
            vector_search_index="cosine_index",
            full_text_search_index="full_text_index",
        )

        retriever = MongoDBAtlasFullTextRetriever(document_store=document_store, filters={"field": "value"}, top_k=5)
        res = retriever.to_dict()
        assert res == {
            "type": "haystack_integrations.components.retrievers.mongodb_atlas.full_text_retriever.MongoDBAtlasFullTextRetriever",  # noqa: E501
            "init_parameters": {
                "document_store": {
                    "type": "haystack_integrations.document_stores.mongodb_atlas.document_store.MongoDBAtlasDocumentStore",  # noqa: E501
                    "init_parameters": {
                        "mongo_connection_string": {
                            "env_vars": ["MONGO_CONNECTION_STRING"],
                            "strict": True,
                            "type": "env_var",
                        },
                        "database_name": "haystack_integration_test",
                        "collection_name": "test_full_text_collection",
                        "vector_search_index": "cosine_index",
                        "full_text_search_index": "full_text_index",
                    },
                },
                "filters": {"field": "value"},
                "top_k": 5,
                "filter_policy": "replace",
            },
        }

    def test_from_dict(self, mock_client, monkeypatch):  # noqa: ARG002  mock_client appears unused but is required
        monkeypatch.setenv("MONGO_CONNECTION_STRING", "test_conn_str")

        data = {
            "type": "haystack_integrations.components.retrievers.mongodb_atlas.full_text_retriever.MongoDBAtlasFullTextRetriever",  # noqa: E501
            "init_parameters": {
                "document_store": {
                    "type": "haystack_integrations.document_stores.mongodb_atlas.document_store.MongoDBAtlasDocumentStore",  # noqa: E501
                    "init_parameters": {
                        "mongo_connection_string": {
                            "env_vars": ["MONGO_CONNECTION_STRING"],
                            "strict": True,
                            "type": "env_var",
                        },
                        "database_name": "haystack_integration_test",
                        "collection_name": "test_full_text_collection",
                        "vector_search_index": "cosine_index",
                        "full_text_search_index": "full_text_index",
                    },
                },
                "filters": {"field": "value"},
                "top_k": 5,
                "filter_policy": "replace",
            },
        }

        retriever = MongoDBAtlasFullTextRetriever.from_dict(data)
        document_store = retriever.document_store

        assert isinstance(document_store, MongoDBAtlasDocumentStore)
        assert isinstance(document_store.mongo_connection_string, EnvVarSecret)
        assert document_store.database_name == "haystack_integration_test"
        assert document_store.collection_name == "test_full_text_collection"
        assert document_store.vector_search_index == "cosine_index"
        assert document_store.full_text_search_index == "full_text_index"
        assert retriever.filters == {"field": "value"}
        assert retriever.top_k == 5
        assert retriever.filter_policy == FilterPolicy.REPLACE

    def test_from_dict_no_filter_policy(self, monkeypatch):  # mock_client appears unused but is required
        monkeypatch.setenv("MONGO_CONNECTION_STRING", "test_conn_str")

        data = {
            "type": "haystack_integrations.components.retrievers.mongodb_atlas.full_text_retriever.MongoDBAtlasFullTextRetriever",  # noqa: E501
            "init_parameters": {
                "document_store": {
                    "type": "haystack_integrations.document_stores.mongodb_atlas.document_store.MongoDBAtlasDocumentStore",  # noqa: E501
                    "init_parameters": {
                        "mongo_connection_string": {
                            "env_vars": ["MONGO_CONNECTION_STRING"],
                            "strict": True,
                            "type": "env_var",
                        },
                        "database_name": "haystack_integration_test",
                        "collection_name": "test_full_text_collection",
                        "vector_search_index": "cosine_index",
                        "full_text_search_index": "full_text_index",
                    },
                },
                "filters": {"field": "value"},
                "top_k": 5,
            },
        }

        retriever = MongoDBAtlasFullTextRetriever.from_dict(data)
        document_store = retriever.document_store

        assert isinstance(document_store, MongoDBAtlasDocumentStore)
        assert isinstance(document_store.mongo_connection_string, EnvVarSecret)
        assert document_store.database_name == "haystack_integration_test"
        assert document_store.collection_name == "test_full_text_collection"
        assert document_store.vector_search_index == "cosine_index"
        assert document_store.full_text_search_index == "full_text_index"
        assert retriever.filters == {"field": "value"}
        assert retriever.top_k == 5
        assert retriever.filter_policy == FilterPolicy.REPLACE

    def test_run(self):
        mock_store = Mock(spec=MongoDBAtlasDocumentStore)
        doc = Document(content="Lorem ipsum")
        mock_store._fulltext_retrieval.return_value = [doc]

        retriever = MongoDBAtlasFullTextRetriever(document_store=mock_store)
        res = retriever.run(query="Lorem ipsum")

        mock_store._fulltext_retrieval.assert_called_once_with(
            query="Lorem ipsum", fuzzy=None, match_criteria=None, score=None, synonyms=None, filters={}, top_k=10
        )

        assert res == {"documents": [doc]}

    def test_run_merge_policy_filter(self):
        mock_store = Mock(spec=MongoDBAtlasDocumentStore)
        doc = Document(content="Lorem ipsum")
        mock_store._fulltext_retrieval.return_value = [doc]

        retriever = MongoDBAtlasFullTextRetriever(
            document_store=mock_store,
            filters={"field": "meta.some_field", "operator": "==", "value": "SomeValue"},
            filter_policy=FilterPolicy.MERGE,
        )
        res = retriever.run(
            query="Lorem ipsum", filters={"field": "meta.some_field", "operator": "==", "value": "Test"}
        )
        # as the both init and run filters are filtering the same field, the run filter takes precedence
        mock_store._fulltext_retrieval.assert_called_once_with(
            query="Lorem ipsum",
            fuzzy=None,
            match_criteria=None,
            score=None,
            synonyms=None,
            filters={"field": "meta.some_field", "operator": "==", "value": "Test"},
            top_k=10,
        )

        assert res == {"documents": [doc]}

    @pytest.mark.asyncio
    async def test_run_async(self):
        mock_store = Mock(spec=MongoDBAtlasDocumentStore)
        doc = Document(content="Lorem ipsum")
        mock_store._fulltext_retrieval_async.return_value = [doc]

        retriever = MongoDBAtlasFullTextRetriever(document_store=mock_store)
        res = await retriever.run_async(query="Lorem ipsum")

        mock_store._fulltext_retrieval_async.assert_called_once_with(
            query="Lorem ipsum", fuzzy=None, match_criteria=None, score=None, synonyms=None, filters={}, top_k=10
        )

        assert res == {"documents": [doc]}

    @pytest.mark.asyncio
    async def test_run_merge_policy_filter_async(self):
        mock_store = Mock(spec=MongoDBAtlasDocumentStore)
        doc = Document(content="Lorem ipsum")
        mock_store._fulltext_retrieval_async.return_value = [doc]

        retriever = MongoDBAtlasFullTextRetriever(
            document_store=mock_store,
            filters={"field": "meta.some_field", "operator": "==", "value": "SomeValue"},
            filter_policy=FilterPolicy.MERGE,
        )
        res = await retriever.run_async(
            query="Lorem ipsum", filters={"field": "meta.some_field", "operator": "==", "value": "Test"}
        )
        # as the both init and run filters are filtering the same field, the run filter takes precedence
        mock_store._fulltext_retrieval_async.assert_called_once_with(
            query="Lorem ipsum",
            fuzzy=None,
            match_criteria=None,
            score=None,
            synonyms=None,
            filters={"field": "meta.some_field", "operator": "==", "value": "Test"},
            top_k=10,
        )

        assert res == {"documents": [doc]}
