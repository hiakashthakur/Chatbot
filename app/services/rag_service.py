import asyncio

from app.prompts.rag_prompt import RAG_PROMPT
from app.exceptions.embedding_exception import EmbeddingException
from app.exceptions.vector_store_exception import VectorStoreException
from app.exceptions.llm_exception import LLMException
from app.logger import logger


class RAGService:

    RRF_K = 60

    def __init__(
        self,
        embedding_service,
        vector_service,
        bm25_service,
        reranker_service,
        query_rewrite_service,
        llm_service,
        memory_service
    ):
        self.embedding_service = embedding_service
        self.vector_service = vector_service
        self.bm25_service = bm25_service
        self.reranker_service = reranker_service
        self.query_rewrite_service = query_rewrite_service
        self.llm_service = llm_service
        self.memory_service = memory_service

    def _apply_rrf(
        self,
        vector_results,
        bm25_results
    ):
        """
        Combine Vector Search and BM25 results
        using Reciprocal Rank Fusion (RRF).

        RRF Score:
            1 / (k + rank)
        """

        logger.info(
            "Applying Reciprocal Rank Fusion"
        )

        documents = {}

        # -------------------------
        # Vector Search Results
        # -------------------------

        vector_documents = vector_results.get(
            "documents",
            [[]]
        )[0]

        vector_sources = vector_results.get(
            "sources",
            [[]]
        )[0]

        vector_pages = vector_results.get(
            "pages",
            [[]]
        )[0]

        vector_chunk_ids = vector_results.get(
            "chunk_ids",
            [[]]
        )[0]

        for rank, (
            document,
            source,
            page,
            chunk_id
        ) in enumerate(
            zip(
                vector_documents,
                vector_sources,
                vector_pages,
                vector_chunk_ids
            ),
            start=1
        ):

            if not document:
                continue

            key = chunk_id or document

            if key not in documents:

                documents[key] = {
                    "document": document,
                    "source": source or "Unknown",
                    "page": page or 0,
                    "chunk_id": chunk_id,
                    "rrf_score": 0.0
                }

            documents[key]["rrf_score"] += (
                1 / (self.RRF_K + rank)
            )

            documents[key]["vector_rank"] = rank

        # -------------------------
        # BM25 Results
        # -------------------------

        for item in bm25_results:

            document = item.get(
                "document",
                ""
            )

            if not document:
                continue

            chunk_id = item.get(
                "chunk_id"
            )

            key = chunk_id or document

            if key not in documents:

                documents[key] = {
                    "document": document,
                    "source": item.get(
                        "source",
                        "Unknown"
                    ),
                    "page": item.get(
                        "page",
                        0
                    ),
                    "chunk_id": chunk_id,
                    "rrf_score": 0.0
                }

            bm25_rank = item.get(
                "bm25_rank"
            )

            if bm25_rank is None:
                continue

            documents[key]["rrf_score"] += (
                1 / (self.RRF_K + bm25_rank)
            )

            documents[key]["bm25_rank"] = bm25_rank

            documents[key]["bm25_score"] = item.get(
                "bm25_score",
                0.0
            )

        # -------------------------
        # Sort by RRF Score
        # -------------------------

        ranked_documents = sorted(
            documents.values(),
            key=lambda item: item["rrf_score"],
            reverse=True
        )

        logger.info(
            f"RRF selected {len(ranked_documents)} unique documents"
        )

        for rank, document in enumerate(
            ranked_documents,
            start=1
        ):
            document["rrf_rank"] = rank

        return ranked_documents

    async def _build_prompt(
        self,
        question: str,
        history: str
    ):
        """
        Rewrite the user query, retrieve documents,
        apply RRF fusion, rerank them and build
        the final RAG prompt.
        """

        # -------------------------
        # Query Rewriting
        # -------------------------

        logger.info(
            "Rewriting user query"
        )

        rewritten_question = (
            await self.query_rewrite_service.rewrite(
                question=question,
                history=history
            )
        )

        logger.info(
            f"Original Question: {question}"
        )

        logger.info(
            f"Rewritten Question: {rewritten_question}"
        )

        # -------------------------
        # Generate Embedding
        # -------------------------

        logger.info(
            "Generating question embedding"
        )

        embedding = await asyncio.to_thread(
            self.embedding_service.get_embedding,
            rewritten_question
        )

        # -------------------------
        # Vector + BM25 Search
        # -------------------------

        logger.info(
            "Searching Vector Store and BM25"
        )

        vector_task = self.vector_service.asearch(
            embedding
        )

        bm25_task = asyncio.to_thread(
            self.bm25_service.search,
            rewritten_question
        )

        vector_results, bm25_results = await asyncio.gather(
            vector_task,
            bm25_task
        )

        # -------------------------
        # RRF Fusion
        # -------------------------

        fused_documents = self._apply_rrf(
            vector_results=vector_results,
            bm25_results=bm25_results
        )

        if not fused_documents:

            logger.warning(
                "No relevant documents found after RRF"
            )

            raise VectorStoreException(
                "No relevant documents found."
            )

        # -------------------------
        # Limit Candidates
        # -------------------------

        # RRF creates the candidate pool.
        # Cross Encoder performs the final ranking.

        candidate_documents = fused_documents[:10]

        logger.info(
            f"RRF candidate documents: "
            f"{len(candidate_documents)}"
        )

        # -------------------------
        # Cross Encoder Reranking
        # -------------------------

        logger.info(
            "Reranking RRF candidates"
        )

        reranked_documents = (
            self.reranker_service.rerank(
                query=rewritten_question,
                documents=candidate_documents
            )
        )

        if not reranked_documents:

            logger.warning(
                "No documents remained after reranking"
            )

            raise VectorStoreException(
                "No relevant documents found after reranking."
            )

        logger.info(
            f"Top {len(reranked_documents)} documents selected"
        )

        # -------------------------
        # Build Context
        # -------------------------

        context = "\n\n".join(
            document["document"]
            for document in reranked_documents
        )

        # -------------------------
        # Final Prompt
        # -------------------------

        # Original question is used for answer generation.
        # Rewritten question is used only for retrieval.

        prompt = RAG_PROMPT.format(
            history=history,
            context=context,
            question=question
        )

        return {
            "prompt": prompt,
            "documents": reranked_documents,
            "rewritten_question": rewritten_question
        }

    async def ask(
        self,
        session_id: str,
        question: str
    ):
        """
        Generate complete RAG response.
        """

        try:

            logger.info(
                f"Processing question for session: {session_id}"
            )

            # -------------------------
            # Conversation History
            # -------------------------

            history = (
                self.memory_service.get_formatted_history(
                    session_id
                )
            )

            # -------------------------
            # Build Prompt
            # -------------------------

            prompt_data = await self._build_prompt(
                question=question,
                history=history
            )

            # -------------------------
            # Generate Answer
            # -------------------------

            answer = await self.llm_service.agenerate(
                prompt_data["prompt"]
            )

            # -------------------------
            # Save Conversation
            # -------------------------

            self.memory_service.add_message(
                session_id=session_id,
                role="user",
                content=question
            )

            self.memory_service.add_message(
                session_id=session_id,
                role="assistant",
                content=answer
            )

            logger.info(
                "Question answered successfully"
            )

            # -------------------------
            # Unique Sources
            # -------------------------

            unique_sources = []

            seen_sources = set()

            for document in prompt_data["documents"]:

                source = document.get(
                    "source",
                    "Unknown"
                )

                page = document.get(
                    "page",
                    0
                )

                key = (
                    source,
                    page
                )

                if key not in seen_sources:

                    seen_sources.add(key)

                    unique_sources.append(
                        {
                            "file": source,
                            "page": page
                        }
                    )

            return {
                "answer": answer,
                "sources": unique_sources
            }

        except (
            EmbeddingException,
            VectorStoreException,
            LLMException
        ):
            raise

        except Exception as e:

            logger.exception(
                "Unexpected error while answering question"
            )

            raise LLMException(
                f"Internal Error: {str(e)}"
            ) from e

    async def stream(
        self,
        session_id: str,
        question: str
    ):
        """
        Stream RAG response.
        """

        try:

            logger.info(
                f"Streaming response for session: {session_id}"
            )

            # -------------------------
            # Conversation History
            # -------------------------

            history = (
                self.memory_service.get_formatted_history(
                    session_id
                )
            )

            # -------------------------
            # Build Prompt
            # -------------------------

            prompt_data = await self._build_prompt(
                question=question,
                history=history
            )

            # -------------------------
            # Stream Response
            # -------------------------

            full_answer = ""

            async for chunk in (
                self.llm_service.astream_generate(
                    prompt_data["prompt"]
                )
            ):

                full_answer += chunk

                yield chunk

            # -------------------------
            # Save Conversation
            # -------------------------

            self.memory_service.add_message(
                session_id=session_id,
                role="user",
                content=question
            )

            self.memory_service.add_message(
                session_id=session_id,
                role="assistant",
                content=full_answer
            )

            logger.info(
                "Streaming completed successfully"
            )

        except (
            EmbeddingException,
            VectorStoreException,
            LLMException
        ) as e:

            logger.exception(
                str(e)
            )

            yield str(e)

        except Exception:

            logger.exception(
                "Unexpected error while streaming response"
            )

            yield "Internal Server Error"