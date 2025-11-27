CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding vector(6)
);

INSERT INTO documents (id, content, metadata, embedding)
VALUES
    (
        1,
        'ASB Secure Gateway uses OPA for real-time policy checks.',
        '{"source": "docs"}',
        '[0.11, 0.23, 0.05, 0.18, 0.42, 0.07]'
    ),
    (
        2,
        'RAG queries run against a pgvector table guarded by policies.',
        '{"source": "docs"}',
        '[0.04, 0.17, 0.29, 0.12, 0.02, 0.33]'
    ),
    (
        3,
        'Agent actions are constrained to a safe tool registry.',
        '{"source": "docs"}',
        '[0.21, 0.09, 0.14, 0.05, 0.27, 0.19]'
    )
ON CONFLICT (id) DO NOTHING;

