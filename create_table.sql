-- Table: public.problems

-- DROP TABLE IF EXISTS public.problems;

CREATE TABLE IF NOT EXISTS public.problems
(
    title text COLLATE pg_catalog."default" NOT NULL,
    topics text[] COLLATE pg_catalog."default" NOT NULL,
    solutions integer,
    difficulty integer,
    link text COLLATE pg_catalog."default" NOT NULL,
    name text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT problems_pkey PRIMARY KEY (title)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.problems
    OWNER to postgres;