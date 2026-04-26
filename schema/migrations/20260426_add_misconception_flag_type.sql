-- Allow misconception flags in student_concept_flags.
-- Idempotent migration: safe to run multiple times.

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_schema = 'public'
          AND table_name = 'student_concept_flags'
          AND constraint_name = 'student_concept_flags_flag_type_check'
    ) THEN
        ALTER TABLE public.student_concept_flags
            DROP CONSTRAINT student_concept_flags_flag_type_check;
    END IF;

    ALTER TABLE public.student_concept_flags
        ADD CONSTRAINT student_concept_flags_flag_type_check
        CHECK (
            flag_type::text = ANY (
                ARRAY[
                    'stuck'::character varying,
                    'at_risk'::character varying,
                    'mastered'::character varying,
                    'needs_quiz'::character varying,
                    'prerequisite_gap'::character varying,
                    'misconception'::character varying
                ]::text[]
            )
        );
END $$;

