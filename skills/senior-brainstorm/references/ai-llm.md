# AI/LLM Integration Architecture

### RAG Pipelines

| Component | Options | Notes |
|-----------|---------|-------|
| Embedding model | OpenAI text-embedding-3-small/large, Cohere embed-v4 | Cost vs quality tradeoff; for FERPA/COPPA consider self-hosted models (student data to third-party APIs) |
| Vector store | pgvector (Supabase native), Pinecone, Qdrant, Weaviate | pgvector for MVP, managed for scale |
| Chunking | Fixed-size (512 tokens), semantic (sentence boundaries) | Semantic preferred for educational content |
| Retrieval | Hybrid (vector + BM25), reranking (Cohere, cross-encoder) | Hybrid retrieval often outperforms pure vector search |
| Orchestration | LangChain, LlamaIndex, custom pipeline | Custom preferred for production |

### AI Tutoring Patterns

1. **Socratic tutor** -- never gives answers directly, asks guiding questions.
   Requires system prompt engineering + output validation.
2. **Adaptive difficulty** -- adjusts content based on learner performance.
   Needs: question bank with difficulty scores, performance tracking, LLM routing.
3. **Content summarizer** -- generates summaries, flashcards, quizzes from course material.
   Pipeline: chunk -> embed -> retrieve relevant -> generate with citations.
4. **Code reviewer** -- reviews student code submissions with educational feedback.
   Requires sandboxed execution + LLM analysis.

### Prompt Orchestration & Observability

| Tool | Purpose | When to use |
|------|---------|------------|
| LangSmith | Trace LLM calls, evaluate outputs, dataset management | Production LLM pipelines |
| Arize Phoenix | Open-source tracing, evals, prompt playground | Budget-constrained, self-hosted |
| Langfuse | Open-source observability, cost tracking, prompt mgmt | Self-hosted alternative to LangSmith |
| Custom logging | Structured JSONL logs with trace IDs | MVP, simple pipelines |

### Guardrails for Educational Content

- **Input validation**: content filters for inappropriate/harmful input (OpenAI moderation API,
  custom classifiers)
- **Output validation**: factual grounding checks, citation requirements, confidence scoring
- **Hallucination prevention**:
  - Always ground responses in retrieved context (RAG, not pure generation)
  - Require citations with page/section references
  - Implement confidence thresholds -- decline to answer below threshold
  - Use structured output (JSON mode) for factual claims
  - Cross-validate generated content against source material
  - Human-in-the-loop review for published educational content
- **Rate limiting**: per-user LLM call budgets, cost caps per session
- **PII filtering**: strip/mask personal data before sending to LLM providers
- **Age-appropriate content**: tone/vocabulary filters for K-12 audiences (COPPA)

### Vector DB Selection Matrix

| Criteria | pgvector | Pinecone | Qdrant | Weaviate |
|----------|----------|----------|--------|----------|
| Setup | In-DB (zero infra) | Managed SaaS | Self-host or cloud | Self-host or cloud |
| Scale | Hardware-dependent (HNSW vs IVFFlat, dimensions, RAM) | 1B+ vectors | 100M+ vectors | 100M+ vectors |
| Filtering | SQL WHERE | Metadata filters | Payload filters | GraphQL filters |
| Cost (MVP) | Free (existing DB) | Managed service (pricing varies) | Free (self-host) | Free (self-host) |
| Best for | MVP, <1M docs | Scale, managed | Performance, hybrid | Multi-modal |

**pgvector scaling note:** pgvector has no hard vector cap. Performance depends on
hardware resources, index type (HNSW for recall, IVFFlat for throughput), vector
dimensions, and query patterns. Benchmark with your actual workload before deciding
to migrate to a dedicated vector DB.
