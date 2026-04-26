-- Add cache metadata columns for /tutor/explain response caching.
-- Idempotent migration: safe to run multiple times.

ALTER TABLE public.messages
    ADD COLUMN IF NOT EXISTS cache_key VARCHAR(32),
    ADD COLUMN IF NOT EXISTS is_cached BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS model_used VARCHAR(50);

CREATE INDEX IF NOT EXISTS idx_messages_ai_tutor_cache_key
    ON public.messages (cache_key)
    WHERE sender = 'ai_tutor' AND cache_key IS NOT NULL;
