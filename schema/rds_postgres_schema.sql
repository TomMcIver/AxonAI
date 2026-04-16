--
-- PostgreSQL database dump
--

\restrict UThYAbo65gXHbsmIwKfPNXHoSzdtW0wAedX6eICuJYIbSxuLegye7vinUjndmuU

-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.9

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: class_concepts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.class_concepts (
    id integer NOT NULL,
    class_id integer NOT NULL,
    concept_id integer NOT NULL
);


--
-- Name: class_concepts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.class_concepts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: class_concepts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.class_concepts_id_seq OWNED BY public.class_concepts.id;


--
-- Name: classes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.classes (
    id integer NOT NULL,
    subject_id integer NOT NULL,
    teacher_id integer NOT NULL,
    name character varying(255) NOT NULL,
    year_level smallint,
    academic_year smallint,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT classes_year_level_check CHECK (((year_level >= 7) AND (year_level <= 13)))
);


--
-- Name: classes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.classes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: classes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.classes_id_seq OWNED BY public.classes.id;


--
-- Name: concept_mastery_states; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.concept_mastery_states (
    id integer NOT NULL,
    student_id integer NOT NULL,
    concept_id integer NOT NULL,
    mastery_score double precision DEFAULT 0,
    confidence double precision DEFAULT 0,
    evidence_count integer DEFAULT 0,
    last_quiz_score double precision,
    last_conversation_outcome character varying(50),
    trend character varying(20) DEFAULT 'stable'::character varying,
    first_assessed_at timestamp with time zone DEFAULT now(),
    last_updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT concept_mastery_states_confidence_check CHECK (((confidence >= (0)::double precision) AND (confidence <= (1)::double precision))),
    CONSTRAINT concept_mastery_states_mastery_score_check CHECK (((mastery_score >= (0)::double precision) AND (mastery_score <= (1)::double precision))),
    CONSTRAINT concept_mastery_states_trend_check CHECK (((trend)::text = ANY ((ARRAY['improving'::character varying, 'stable'::character varying, 'declining'::character varying])::text[])))
);


--
-- Name: concept_mastery_states_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.concept_mastery_states_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: concept_mastery_states_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.concept_mastery_states_id_seq OWNED BY public.concept_mastery_states.id;


--
-- Name: concept_prerequisites; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.concept_prerequisites (
    id integer NOT NULL,
    concept_id integer NOT NULL,
    prerequisite_concept_id integer NOT NULL,
    strength double precision DEFAULT 1.0,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT concept_prerequisites_check CHECK ((concept_id <> prerequisite_concept_id)),
    CONSTRAINT concept_prerequisites_strength_check CHECK (((strength >= (0)::double precision) AND (strength <= (1)::double precision)))
);


--
-- Name: concept_prerequisites_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.concept_prerequisites_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: concept_prerequisites_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.concept_prerequisites_id_seq OWNED BY public.concept_prerequisites.id;


--
-- Name: concepts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.concepts (
    id integer NOT NULL,
    subject_id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    difficulty_level smallint,
    year_level_introduced smallint,
    concept_type character varying(50),
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT concepts_concept_type_check CHECK (((concept_type)::text = ANY ((ARRAY['foundational'::character varying, 'procedural'::character varying, 'conceptual'::character varying, 'applied'::character varying])::text[]))),
    CONSTRAINT concepts_difficulty_level_check CHECK (((difficulty_level >= 1) AND (difficulty_level <= 10))),
    CONSTRAINT concepts_year_level_introduced_check CHECK (((year_level_introduced >= 7) AND (year_level_introduced <= 13)))
);


--
-- Name: concepts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.concepts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: concepts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.concepts_id_seq OWNED BY public.concepts.id;


--
-- Name: content_chunks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.content_chunks (
    id integer NOT NULL,
    teacher_content_id integer NOT NULL,
    class_id integer NOT NULL,
    concept_id integer,
    chunk_text text NOT NULL,
    chunk_index integer NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: content_chunks_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.content_chunks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: content_chunks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.content_chunks_id_seq OWNED BY public.content_chunks.id;


--
-- Name: conversations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conversations (
    id integer NOT NULL,
    student_id integer NOT NULL,
    class_id integer NOT NULL,
    concept_id integer,
    started_at timestamp with time zone DEFAULT now(),
    ended_at timestamp with time zone,
    total_messages integer DEFAULT 0,
    lightbulb_moment_detected boolean DEFAULT false,
    lightbulb_message_index integer,
    session_engagement_score double precision,
    primary_teaching_approach character varying(100),
    outcome character varying(50),
    notes text,
    CONSTRAINT conversations_outcome_check CHECK (((outcome)::text = ANY ((ARRAY['resolved'::character varying, 'unresolved'::character varying, 'partially_resolved'::character varying, 'abandoned'::character varying])::text[]))),
    CONSTRAINT conversations_session_engagement_score_check CHECK (((session_engagement_score >= (0)::double precision) AND (session_engagement_score <= (1)::double precision)))
);


--
-- Name: conversations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.conversations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: conversations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.conversations_id_seq OWNED BY public.conversations.id;


--
-- Name: messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.messages (
    id integer NOT NULL,
    conversation_id integer NOT NULL,
    student_id integer NOT NULL,
    sender character varying(10) NOT NULL,
    content text NOT NULL,
    message_index integer NOT NULL,
    sent_at timestamp with time zone DEFAULT now(),
    response_time_seconds double precision,
    teaching_approach character varying(100),
    concept_id integer,
    is_lightbulb_moment boolean DEFAULT false,
    frustration_signal boolean DEFAULT false,
    engagement_signal character varying(50),
    word_count integer,
    character_count integer,
    CONSTRAINT messages_engagement_signal_check CHECK (((engagement_signal)::text = ANY ((ARRAY['engaged'::character varying, 'neutral'::character varying, 'disengaged'::character varying, 'confused'::character varying])::text[]))),
    CONSTRAINT messages_sender_check CHECK (((sender)::text = ANY ((ARRAY['student'::character varying, 'ai'::character varying])::text[])))
);


--
-- Name: messages_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.messages_id_seq OWNED BY public.messages.id;


--
-- Name: model_predictions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.model_predictions (
    id integer NOT NULL,
    student_id integer NOT NULL,
    model_name character varying(100) NOT NULL,
    prediction_type character varying(100) NOT NULL,
    prediction_value jsonb NOT NULL,
    confidence double precision,
    input_features_snapshot jsonb,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT model_predictions_confidence_check CHECK (((confidence >= (0)::double precision) AND (confidence <= (1)::double precision)))
);


--
-- Name: model_predictions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_predictions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: model_predictions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.model_predictions_id_seq OWNED BY public.model_predictions.id;


--
-- Name: pedagogical_memory; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pedagogical_memory (
    id integer NOT NULL,
    student_id integer NOT NULL,
    teaching_approach character varying(100) NOT NULL,
    concept_type character varying(50),
    success_count integer DEFAULT 0,
    attempt_count integer DEFAULT 0,
    success_rate double precision DEFAULT 0,
    avg_messages_to_lightbulb double precision,
    last_used_at timestamp with time zone,
    last_successful_at timestamp with time zone,
    CONSTRAINT pedagogical_memory_concept_type_check CHECK (((concept_type)::text = ANY ((ARRAY['foundational'::character varying, 'procedural'::character varying, 'conceptual'::character varying, 'applied'::character varying])::text[]))),
    CONSTRAINT pedagogical_memory_success_rate_check CHECK (((success_rate >= (0)::double precision) AND (success_rate <= (1)::double precision)))
);


--
-- Name: pedagogical_memory_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.pedagogical_memory_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: pedagogical_memory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pedagogical_memory_id_seq OWNED BY public.pedagogical_memory.id;


--
-- Name: quiz_questions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.quiz_questions (
    id integer NOT NULL,
    quiz_session_id integer NOT NULL,
    concept_id integer NOT NULL,
    question_text text NOT NULL,
    question_type character varying(50),
    correct_answer text,
    student_answer text,
    is_correct boolean,
    time_taken_seconds double precision,
    difficulty_level double precision,
    diagnostic_purpose text,
    prerequisite_concept_id integer,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT quiz_questions_difficulty_level_check CHECK (((difficulty_level >= (0)::double precision) AND (difficulty_level <= (1)::double precision))),
    CONSTRAINT quiz_questions_question_type_check CHECK (((question_type)::text = ANY ((ARRAY['multiple_choice'::character varying, 'short_answer'::character varying, 'worked_example'::character varying])::text[])))
);


--
-- Name: quiz_questions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.quiz_questions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: quiz_questions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.quiz_questions_id_seq OWNED BY public.quiz_questions.id;


--
-- Name: quiz_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.quiz_sessions (
    id integer NOT NULL,
    student_id integer NOT NULL,
    class_id integer NOT NULL,
    concept_id integer NOT NULL,
    conversation_id integer,
    triggered_by character varying(50),
    started_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone,
    total_questions integer DEFAULT 0,
    correct_answers integer DEFAULT 0,
    score_percentage double precision,
    diagnosis_outcome text,
    CONSTRAINT quiz_sessions_score_percentage_check CHECK (((score_percentage >= (0)::double precision) AND (score_percentage <= (100)::double precision))),
    CONSTRAINT quiz_sessions_triggered_by_check CHECK (((triggered_by)::text = ANY ((ARRAY['ai_initiated'::character varying, 'teacher_initiated'::character varying, 'scheduled'::character varying])::text[])))
);


--
-- Name: quiz_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.quiz_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: quiz_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.quiz_sessions_id_seq OWNED BY public.quiz_sessions.id;


--
-- Name: student_classes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.student_classes (
    id integer NOT NULL,
    student_id integer NOT NULL,
    class_id integer NOT NULL,
    enrolled_at timestamp with time zone DEFAULT now(),
    is_active boolean DEFAULT true
);


--
-- Name: student_classes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.student_classes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: student_classes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.student_classes_id_seq OWNED BY public.student_classes.id;


--
-- Name: student_concept_flags; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.student_concept_flags (
    id integer NOT NULL,
    student_id integer NOT NULL,
    concept_id integer NOT NULL,
    flag_type character varying(50),
    flag_detail text,
    root_cause_concept_id integer,
    raised_at timestamp with time zone DEFAULT now(),
    resolved_at timestamp with time zone,
    is_active boolean DEFAULT true,
    recommended_intervention text,
    CONSTRAINT student_concept_flags_flag_type_check CHECK (((flag_type)::text = ANY ((ARRAY['stuck'::character varying, 'at_risk'::character varying, 'mastered'::character varying, 'needs_quiz'::character varying, 'prerequisite_gap'::character varying])::text[])))
);


--
-- Name: student_concept_flags_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.student_concept_flags_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: student_concept_flags_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.student_concept_flags_id_seq OWNED BY public.student_concept_flags.id;


--
-- Name: student_learning_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.student_learning_profiles (
    id integer NOT NULL,
    student_id integer NOT NULL,
    dominant_learning_style character varying(100),
    best_time_of_day character varying(50),
    average_response_time_seconds double precision,
    frustration_threshold double precision,
    prefers_short_explanations boolean DEFAULT false,
    prefers_encouragement boolean DEFAULT true,
    average_session_length_minutes double precision,
    total_interactions integer DEFAULT 0,
    last_interaction_at timestamp with time zone,
    overall_mastery_trend character varying(50) DEFAULT 'stable'::character varying,
    overall_engagement_score double precision,
    overall_risk_score double precision,
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT student_learning_profiles_frustration_threshold_check CHECK (((frustration_threshold >= (0)::double precision) AND (frustration_threshold <= (1)::double precision))),
    CONSTRAINT student_learning_profiles_overall_engagement_score_check CHECK (((overall_engagement_score >= (0)::double precision) AND (overall_engagement_score <= (1)::double precision))),
    CONSTRAINT student_learning_profiles_overall_risk_score_check CHECK (((overall_risk_score >= (0)::double precision) AND (overall_risk_score <= (1)::double precision)))
);


--
-- Name: student_learning_profiles_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.student_learning_profiles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: student_learning_profiles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.student_learning_profiles_id_seq OWNED BY public.student_learning_profiles.id;


--
-- Name: student_wellbeing_context; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.student_wellbeing_context (
    id integer NOT NULL,
    student_id integer NOT NULL,
    has_learning_support_plan boolean DEFAULT false,
    learning_support_details text,
    has_medical_condition boolean DEFAULT false,
    medical_details text,
    home_situation_flag boolean DEFAULT false,
    home_situation_notes text,
    is_esol boolean DEFAULT false,
    attendance_percentage double precision,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT student_wellbeing_context_attendance_percentage_check CHECK (((attendance_percentage >= (0)::double precision) AND (attendance_percentage <= (100)::double precision)))
);


--
-- Name: student_wellbeing_context_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.student_wellbeing_context_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: student_wellbeing_context_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.student_wellbeing_context_id_seq OWNED BY public.student_wellbeing_context.id;


--
-- Name: students; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.students (
    id integer NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    date_of_birth date,
    year_level smallint,
    gender character varying(50),
    ethnicity character varying(100),
    is_demo_student boolean DEFAULT false,
    is_background_student boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT students_year_level_check CHECK (((year_level >= 7) AND (year_level <= 13)))
);


--
-- Name: students_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.students_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: students_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.students_id_seq OWNED BY public.students.id;


--
-- Name: subjects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.subjects (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: subjects_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.subjects_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: subjects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.subjects_id_seq OWNED BY public.subjects.id;


--
-- Name: teacher_ai_insights; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.teacher_ai_insights (
    id integer NOT NULL,
    student_id integer NOT NULL,
    teacher_id integer NOT NULL,
    class_id integer NOT NULL,
    student_summary text,
    risk_narrative text,
    recommended_interventions text,
    teaching_approach_advice text,
    generated_at timestamp with time zone DEFAULT now(),
    model_used character varying(50)
);


--
-- Name: teacher_ai_insights_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.teacher_ai_insights_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: teacher_ai_insights_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.teacher_ai_insights_id_seq OWNED BY public.teacher_ai_insights.id;


--
-- Name: teacher_content; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.teacher_content (
    id integer NOT NULL,
    class_id integer NOT NULL,
    teacher_id integer NOT NULL,
    file_name character varying(255) NOT NULL,
    file_type character varying(50),
    s3_key character varying(500),
    processing_status character varying(50) DEFAULT 'pending'::character varying,
    concept_tags integer[],
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT teacher_content_processing_status_check CHECK (((processing_status)::text = ANY ((ARRAY['pending'::character varying, 'processed'::character varying, 'failed'::character varying])::text[])))
);


--
-- Name: teacher_content_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.teacher_content_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: teacher_content_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.teacher_content_id_seq OWNED BY public.teacher_content.id;


--
-- Name: teacher_interventions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.teacher_interventions (
    id integer NOT NULL,
    teacher_id integer NOT NULL,
    class_id integer NOT NULL,
    intervention_type character varying(50),
    student_ids integer[],
    concept_id integer NOT NULL,
    recommended_action text,
    likelihood_of_success double precision,
    students_sharing_gap integer,
    created_at timestamp with time zone DEFAULT now(),
    teacher_actioned boolean DEFAULT false,
    actioned_at timestamp with time zone,
    outcome_notes text,
    CONSTRAINT teacher_interventions_intervention_type_check CHECK (((intervention_type)::text = ANY ((ARRAY['individual'::character varying, 'group'::character varying, 'whole_class'::character varying])::text[]))),
    CONSTRAINT teacher_interventions_likelihood_of_success_check CHECK (((likelihood_of_success >= (0)::double precision) AND (likelihood_of_success <= (1)::double precision)))
);


--
-- Name: teacher_interventions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.teacher_interventions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: teacher_interventions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.teacher_interventions_id_seq OWNED BY public.teacher_interventions.id;


--
-- Name: teachers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.teachers (
    id integer NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    email character varying(255) NOT NULL,
    is_demo_teacher boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: teachers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.teachers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: teachers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.teachers_id_seq OWNED BY public.teachers.id;


--
-- Name: class_concepts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.class_concepts ALTER COLUMN id SET DEFAULT nextval('public.class_concepts_id_seq'::regclass);


--
-- Name: classes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classes ALTER COLUMN id SET DEFAULT nextval('public.classes_id_seq'::regclass);


--
-- Name: concept_mastery_states id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.concept_mastery_states ALTER COLUMN id SET DEFAULT nextval('public.concept_mastery_states_id_seq'::regclass);


--
-- Name: concept_prerequisites id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.concept_prerequisites ALTER COLUMN id SET DEFAULT nextval('public.concept_prerequisites_id_seq'::regclass);


--
-- Name: concepts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.concepts ALTER COLUMN id SET DEFAULT nextval('public.concepts_id_seq'::regclass);


--
-- Name: content_chunks id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.content_chunks ALTER COLUMN id SET DEFAULT nextval('public.content_chunks_id_seq'::regclass);


--
-- Name: conversations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations ALTER COLUMN id SET DEFAULT nextval('public.conversations_id_seq'::regclass);


--
-- Name: messages id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages ALTER COLUMN id SET DEFAULT nextval('public.messages_id_seq'::regclass);


--
-- Name: model_predictions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_predictions ALTER COLUMN id SET DEFAULT nextval('public.model_predictions_id_seq'::regclass);


--
-- Name: pedagogical_memory id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pedagogical_memory ALTER COLUMN id SET DEFAULT nextval('public.pedagogical_memory_id_seq'::regclass);


--
-- Name: quiz_questions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_questions ALTER COLUMN id SET DEFAULT nextval('public.quiz_questions_id_seq'::regclass);


--
-- Name: quiz_sessions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_sessions ALTER COLUMN id SET DEFAULT nextval('public.quiz_sessions_id_seq'::regclass);


--
-- Name: student_classes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_classes ALTER COLUMN id SET DEFAULT nextval('public.student_classes_id_seq'::regclass);


--
-- Name: student_concept_flags id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_concept_flags ALTER COLUMN id SET DEFAULT nextval('public.student_concept_flags_id_seq'::regclass);


--
-- Name: student_learning_profiles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_learning_profiles ALTER COLUMN id SET DEFAULT nextval('public.student_learning_profiles_id_seq'::regclass);


--
-- Name: student_wellbeing_context id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_wellbeing_context ALTER COLUMN id SET DEFAULT nextval('public.student_wellbeing_context_id_seq'::regclass);


--
-- Name: students id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.students ALTER COLUMN id SET DEFAULT nextval('public.students_id_seq'::regclass);


--
-- Name: subjects id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subjects ALTER COLUMN id SET DEFAULT nextval('public.subjects_id_seq'::regclass);


--
-- Name: teacher_ai_insights id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_ai_insights ALTER COLUMN id SET DEFAULT nextval('public.teacher_ai_insights_id_seq'::regclass);


--
-- Name: teacher_content id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_content ALTER COLUMN id SET DEFAULT nextval('public.teacher_content_id_seq'::regclass);


--
-- Name: teacher_interventions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_interventions ALTER COLUMN id SET DEFAULT nextval('public.teacher_interventions_id_seq'::regclass);


--
-- Name: teachers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teachers ALTER COLUMN id SET DEFAULT nextval('public.teachers_id_seq'::regclass);


--
-- Name: class_concepts class_concepts_class_id_concept_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.class_concepts
    ADD CONSTRAINT class_concepts_class_id_concept_id_key UNIQUE (class_id, concept_id);


--
-- Name: class_concepts class_concepts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.class_concepts
    ADD CONSTRAINT class_concepts_pkey PRIMARY KEY (id);


--
-- Name: classes classes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classes
    ADD CONSTRAINT classes_pkey PRIMARY KEY (id);


--
-- Name: concept_mastery_states concept_mastery_states_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.concept_mastery_states
    ADD CONSTRAINT concept_mastery_states_pkey PRIMARY KEY (id);


--
-- Name: concept_mastery_states concept_mastery_states_student_id_concept_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.concept_mastery_states
    ADD CONSTRAINT concept_mastery_states_student_id_concept_id_key UNIQUE (student_id, concept_id);


--
-- Name: concept_prerequisites concept_prerequisites_concept_id_prerequisite_concept_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.concept_prerequisites
    ADD CONSTRAINT concept_prerequisites_concept_id_prerequisite_concept_id_key UNIQUE (concept_id, prerequisite_concept_id);


--
-- Name: concept_prerequisites concept_prerequisites_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.concept_prerequisites
    ADD CONSTRAINT concept_prerequisites_pkey PRIMARY KEY (id);


--
-- Name: concepts concepts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.concepts
    ADD CONSTRAINT concepts_pkey PRIMARY KEY (id);


--
-- Name: content_chunks content_chunks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.content_chunks
    ADD CONSTRAINT content_chunks_pkey PRIMARY KEY (id);


--
-- Name: conversations conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_pkey PRIMARY KEY (id);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);


--
-- Name: model_predictions model_predictions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_predictions
    ADD CONSTRAINT model_predictions_pkey PRIMARY KEY (id);


--
-- Name: pedagogical_memory pedagogical_memory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pedagogical_memory
    ADD CONSTRAINT pedagogical_memory_pkey PRIMARY KEY (id);


--
-- Name: pedagogical_memory pedagogical_memory_student_id_teaching_approach_concept_typ_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pedagogical_memory
    ADD CONSTRAINT pedagogical_memory_student_id_teaching_approach_concept_typ_key UNIQUE (student_id, teaching_approach, concept_type);


--
-- Name: quiz_questions quiz_questions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_questions
    ADD CONSTRAINT quiz_questions_pkey PRIMARY KEY (id);


--
-- Name: quiz_sessions quiz_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_sessions
    ADD CONSTRAINT quiz_sessions_pkey PRIMARY KEY (id);


--
-- Name: student_classes student_classes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_classes
    ADD CONSTRAINT student_classes_pkey PRIMARY KEY (id);


--
-- Name: student_classes student_classes_student_id_class_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_classes
    ADD CONSTRAINT student_classes_student_id_class_id_key UNIQUE (student_id, class_id);


--
-- Name: student_concept_flags student_concept_flags_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_concept_flags
    ADD CONSTRAINT student_concept_flags_pkey PRIMARY KEY (id);


--
-- Name: student_learning_profiles student_learning_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_learning_profiles
    ADD CONSTRAINT student_learning_profiles_pkey PRIMARY KEY (id);


--
-- Name: student_learning_profiles student_learning_profiles_student_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_learning_profiles
    ADD CONSTRAINT student_learning_profiles_student_id_key UNIQUE (student_id);


--
-- Name: student_wellbeing_context student_wellbeing_context_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_wellbeing_context
    ADD CONSTRAINT student_wellbeing_context_pkey PRIMARY KEY (id);


--
-- Name: students students_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_pkey PRIMARY KEY (id);


--
-- Name: subjects subjects_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subjects
    ADD CONSTRAINT subjects_name_key UNIQUE (name);


--
-- Name: subjects subjects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subjects
    ADD CONSTRAINT subjects_pkey PRIMARY KEY (id);


--
-- Name: teacher_ai_insights teacher_ai_insights_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_ai_insights
    ADD CONSTRAINT teacher_ai_insights_pkey PRIMARY KEY (id);


--
-- Name: teacher_ai_insights teacher_ai_insights_student_id_class_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_ai_insights
    ADD CONSTRAINT teacher_ai_insights_student_id_class_id_key UNIQUE (student_id, class_id);


--
-- Name: teacher_content teacher_content_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_content
    ADD CONSTRAINT teacher_content_pkey PRIMARY KEY (id);


--
-- Name: teacher_interventions teacher_interventions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_interventions
    ADD CONSTRAINT teacher_interventions_pkey PRIMARY KEY (id);


--
-- Name: teachers teachers_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teachers
    ADD CONSTRAINT teachers_email_key UNIQUE (email);


--
-- Name: teachers teachers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teachers
    ADD CONSTRAINT teachers_pkey PRIMARY KEY (id);


--
-- Name: idx_conversations_class; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conversations_class ON public.conversations USING btree (class_id);


--
-- Name: idx_conversations_student; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conversations_student ON public.conversations USING btree (student_id);


--
-- Name: idx_flags_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_flags_active ON public.student_concept_flags USING btree (is_active) WHERE (is_active = true);


--
-- Name: idx_flags_student; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_flags_student ON public.student_concept_flags USING btree (student_id);


--
-- Name: idx_mastery_concept; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mastery_concept ON public.concept_mastery_states USING btree (concept_id);


--
-- Name: idx_mastery_student; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mastery_student ON public.concept_mastery_states USING btree (student_id);


--
-- Name: idx_messages_conversation; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_messages_conversation ON public.messages USING btree (conversation_id);


--
-- Name: idx_messages_student; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_messages_student ON public.messages USING btree (student_id);


--
-- Name: idx_pedagogy_student; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pedagogy_student ON public.pedagogical_memory USING btree (student_id);


--
-- Name: idx_predictions_student; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_predictions_student ON public.model_predictions USING btree (student_id);


--
-- Name: idx_prerequisites_concept; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prerequisites_concept ON public.concept_prerequisites USING btree (concept_id);


--
-- Name: idx_prerequisites_prereq; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prerequisites_prereq ON public.concept_prerequisites USING btree (prerequisite_concept_id);


--
-- Name: idx_quiz_questions_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_quiz_questions_session ON public.quiz_questions USING btree (quiz_session_id);


--
-- Name: idx_student_classes_student; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_student_classes_student ON public.student_classes USING btree (student_id);


--
-- Name: class_concepts class_concepts_class_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.class_concepts
    ADD CONSTRAINT class_concepts_class_id_fkey FOREIGN KEY (class_id) REFERENCES public.classes(id);


--
-- Name: class_concepts class_concepts_concept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.class_concepts
    ADD CONSTRAINT class_concepts_concept_id_fkey FOREIGN KEY (concept_id) REFERENCES public.concepts(id);


--
-- Name: classes classes_subject_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classes
    ADD CONSTRAINT classes_subject_id_fkey FOREIGN KEY (subject_id) REFERENCES public.subjects(id);


--
-- Name: classes classes_teacher_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classes
    ADD CONSTRAINT classes_teacher_id_fkey FOREIGN KEY (teacher_id) REFERENCES public.teachers(id);


--
-- Name: concept_mastery_states concept_mastery_states_concept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.concept_mastery_states
    ADD CONSTRAINT concept_mastery_states_concept_id_fkey FOREIGN KEY (concept_id) REFERENCES public.concepts(id);


--
-- Name: concept_mastery_states concept_mastery_states_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.concept_mastery_states
    ADD CONSTRAINT concept_mastery_states_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.students(id);


--
-- Name: concept_prerequisites concept_prerequisites_concept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.concept_prerequisites
    ADD CONSTRAINT concept_prerequisites_concept_id_fkey FOREIGN KEY (concept_id) REFERENCES public.concepts(id);


--
-- Name: concept_prerequisites concept_prerequisites_prerequisite_concept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.concept_prerequisites
    ADD CONSTRAINT concept_prerequisites_prerequisite_concept_id_fkey FOREIGN KEY (prerequisite_concept_id) REFERENCES public.concepts(id);


--
-- Name: concepts concepts_subject_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.concepts
    ADD CONSTRAINT concepts_subject_id_fkey FOREIGN KEY (subject_id) REFERENCES public.subjects(id);


--
-- Name: content_chunks content_chunks_class_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.content_chunks
    ADD CONSTRAINT content_chunks_class_id_fkey FOREIGN KEY (class_id) REFERENCES public.classes(id);


--
-- Name: content_chunks content_chunks_concept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.content_chunks
    ADD CONSTRAINT content_chunks_concept_id_fkey FOREIGN KEY (concept_id) REFERENCES public.concepts(id);


--
-- Name: content_chunks content_chunks_teacher_content_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.content_chunks
    ADD CONSTRAINT content_chunks_teacher_content_id_fkey FOREIGN KEY (teacher_content_id) REFERENCES public.teacher_content(id);


--
-- Name: conversations conversations_class_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_class_id_fkey FOREIGN KEY (class_id) REFERENCES public.classes(id);


--
-- Name: conversations conversations_concept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_concept_id_fkey FOREIGN KEY (concept_id) REFERENCES public.concepts(id);


--
-- Name: conversations conversations_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.students(id);


--
-- Name: messages messages_concept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_concept_id_fkey FOREIGN KEY (concept_id) REFERENCES public.concepts(id);


--
-- Name: messages messages_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id);


--
-- Name: messages messages_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.students(id);


--
-- Name: model_predictions model_predictions_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_predictions
    ADD CONSTRAINT model_predictions_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.students(id);


--
-- Name: pedagogical_memory pedagogical_memory_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pedagogical_memory
    ADD CONSTRAINT pedagogical_memory_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.students(id);


--
-- Name: quiz_questions quiz_questions_concept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_questions
    ADD CONSTRAINT quiz_questions_concept_id_fkey FOREIGN KEY (concept_id) REFERENCES public.concepts(id);


--
-- Name: quiz_questions quiz_questions_prerequisite_concept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_questions
    ADD CONSTRAINT quiz_questions_prerequisite_concept_id_fkey FOREIGN KEY (prerequisite_concept_id) REFERENCES public.concepts(id);


--
-- Name: quiz_questions quiz_questions_quiz_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_questions
    ADD CONSTRAINT quiz_questions_quiz_session_id_fkey FOREIGN KEY (quiz_session_id) REFERENCES public.quiz_sessions(id);


--
-- Name: quiz_sessions quiz_sessions_class_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_sessions
    ADD CONSTRAINT quiz_sessions_class_id_fkey FOREIGN KEY (class_id) REFERENCES public.classes(id);


--
-- Name: quiz_sessions quiz_sessions_concept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_sessions
    ADD CONSTRAINT quiz_sessions_concept_id_fkey FOREIGN KEY (concept_id) REFERENCES public.concepts(id);


--
-- Name: quiz_sessions quiz_sessions_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_sessions
    ADD CONSTRAINT quiz_sessions_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id);


--
-- Name: quiz_sessions quiz_sessions_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_sessions
    ADD CONSTRAINT quiz_sessions_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.students(id);


--
-- Name: student_classes student_classes_class_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_classes
    ADD CONSTRAINT student_classes_class_id_fkey FOREIGN KEY (class_id) REFERENCES public.classes(id);


--
-- Name: student_classes student_classes_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_classes
    ADD CONSTRAINT student_classes_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.students(id);


--
-- Name: student_concept_flags student_concept_flags_concept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_concept_flags
    ADD CONSTRAINT student_concept_flags_concept_id_fkey FOREIGN KEY (concept_id) REFERENCES public.concepts(id);


--
-- Name: student_concept_flags student_concept_flags_root_cause_concept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_concept_flags
    ADD CONSTRAINT student_concept_flags_root_cause_concept_id_fkey FOREIGN KEY (root_cause_concept_id) REFERENCES public.concepts(id);


--
-- Name: student_concept_flags student_concept_flags_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_concept_flags
    ADD CONSTRAINT student_concept_flags_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.students(id);


--
-- Name: student_learning_profiles student_learning_profiles_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_learning_profiles
    ADD CONSTRAINT student_learning_profiles_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.students(id) ON DELETE CASCADE;


--
-- Name: student_wellbeing_context student_wellbeing_context_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_wellbeing_context
    ADD CONSTRAINT student_wellbeing_context_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.students(id) ON DELETE CASCADE;


--
-- Name: teacher_content teacher_content_class_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_content
    ADD CONSTRAINT teacher_content_class_id_fkey FOREIGN KEY (class_id) REFERENCES public.classes(id);


--
-- Name: teacher_content teacher_content_teacher_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_content
    ADD CONSTRAINT teacher_content_teacher_id_fkey FOREIGN KEY (teacher_id) REFERENCES public.teachers(id);


--
-- Name: teacher_interventions teacher_interventions_class_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_interventions
    ADD CONSTRAINT teacher_interventions_class_id_fkey FOREIGN KEY (class_id) REFERENCES public.classes(id);


--
-- Name: teacher_interventions teacher_interventions_concept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_interventions
    ADD CONSTRAINT teacher_interventions_concept_id_fkey FOREIGN KEY (concept_id) REFERENCES public.concepts(id);


--
-- Name: teacher_interventions teacher_interventions_teacher_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teacher_interventions
    ADD CONSTRAINT teacher_interventions_teacher_id_fkey FOREIGN KEY (teacher_id) REFERENCES public.teachers(id);


--
-- PostgreSQL database dump complete
--

\unrestrict UThYAbo65gXHbsmIwKfPNXHoSzdtW0wAedX6eICuJYIbSxuLegye7vinUjndmuU

