--
-- PostgreSQL database dump
--

\restrict 1edMWlM0T4foK3FgHsed58xntoY0oaGVE3Q8x6ELxq5aQur5sWFVu0Xgeb1ENzP

-- Dumped from database version 16.13 (Ubuntu 16.13-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.13 (Ubuntu 16.13-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: diagnoses; Type: TABLE; Schema: public; Owner: sambomatic
--

CREATE TABLE public.diagnoses (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    serum_creatinine double precision NOT NULL,
    urine_acr double precision NOT NULL,
    patient_age integer NOT NULL,
    patient_gender character varying(10) NOT NULL,
    blood_pressure integer,
    specific_gravity double precision,
    albumin integer,
    sugar_level integer,
    red_blood_cells character varying(20),
    blood_urea double precision,
    sodium double precision,
    potassium double precision,
    hemoglobin double precision,
    white_blood_cell_count integer,
    diabetes_mellitus character varying(10),
    hypertension character varying(10),
    egfr double precision NOT NULL,
    gfr_stage character varying(10) NOT NULL,
    albuminuria_stage character varying(10) NOT NULL,
    risk_level character varying(20) NOT NULL,
    recommendation text NOT NULL,
    ml_prediction character varying(20),
    ml_confidence double precision,
    gemini_report json,
    diagnosed_by integer NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.diagnoses OWNER TO sambomatic;

--
-- Name: diagnoses_id_seq; Type: SEQUENCE; Schema: public; Owner: sambomatic
--

CREATE SEQUENCE public.diagnoses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.diagnoses_id_seq OWNER TO sambomatic;

--
-- Name: diagnoses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: sambomatic
--

ALTER SEQUENCE public.diagnoses_id_seq OWNED BY public.diagnoses.id;


--
-- Name: patients; Type: TABLE; Schema: public; Owner: sambomatic
--

CREATE TABLE public.patients (
    id integer NOT NULL,
    patient_id character varying(50) NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    age integer NOT NULL,
    gender character varying(10) NOT NULL,
    phone character varying(20),
    created_at timestamp without time zone,
    created_by integer NOT NULL
);


ALTER TABLE public.patients OWNER TO sambomatic;

--
-- Name: patients_id_seq; Type: SEQUENCE; Schema: public; Owner: sambomatic
--

CREATE SEQUENCE public.patients_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.patients_id_seq OWNER TO sambomatic;

--
-- Name: patients_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: sambomatic
--

ALTER SEQUENCE public.patients_id_seq OWNED BY public.patients.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: sambomatic
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(80) NOT NULL,
    password_hash character varying(256) NOT NULL,
    full_name character varying(150) NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.users OWNER TO sambomatic;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: sambomatic
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO sambomatic;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: sambomatic
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: diagnoses id; Type: DEFAULT; Schema: public; Owner: sambomatic
--

ALTER TABLE ONLY public.diagnoses ALTER COLUMN id SET DEFAULT nextval('public.diagnoses_id_seq'::regclass);


--
-- Name: patients id; Type: DEFAULT; Schema: public; Owner: sambomatic
--

ALTER TABLE ONLY public.patients ALTER COLUMN id SET DEFAULT nextval('public.patients_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: sambomatic
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: diagnoses; Type: TABLE DATA; Schema: public; Owner: sambomatic
--

COPY public.diagnoses (id, patient_id, serum_creatinine, urine_acr, patient_age, patient_gender, blood_pressure, specific_gravity, albumin, sugar_level, red_blood_cells, blood_urea, sodium, potassium, hemoglobin, white_blood_cell_count, diabetes_mellitus, hypertension, egfr, gfr_stage, albuminuria_stage, risk_level, recommendation, ml_prediction, ml_confidence, gemini_report, diagnosed_by, created_at) FROM stdin;
1	1	1.2	150	45	Female	120	1.02	1	0	normal	40	138	4.2	14.5	8000	no	no	56.89	G3a	A2	High	High risk of CKD progression. Refer to nephrology if not already under specialist care. Intensify blood pressure and glycaemic control. Monitor eGFR and ACR every 3–4 months. Evaluate for complications (anaemia, bone disease, acidosis).	No CKD Detected	1	{"medical_insights": "Based on the Decision Tree model trained on the UCI CKD dataset, the patient is classified as 'No CKD Detected' with a confidence of 100%.  Serum Creatinine (1.2 mg/dL) is elevated above normal gender thresholds, pointing towards reduced glomerular filtration.", "risk_analysis": "Risk analysis suggests active kidney damage or impaired filtration function. The presence of risk factors needs urgent monitoring to prevent progressive loss of nephrons.", "suggested_precautions": ["Review all prescriptions; avoid nephrotoxic drugs, especially NSAIDs (e.g., ibuprofen, naproxen).", "Ensure adequate hydration, matching fluid intake with output levels.", "Consult a nephrologist if GFR drops below 30 mL/min/1.73 m\\u00b2."], "lifestyle_recommendations": ["Maintain low-sodium dietary habits to protect baseline vascular pressure.", "Engage in moderate physical activity for 30 minutes, 5 days a week.", "Cease smoking immediately, as nicotine accelerates renal microvascular deterioration.", "Limit high-protein diets; target moderate intake (0.8 g/kg body weight) to reduce glomerular load."], "follow_up_recommendations": ["Re-check Serum Creatinine and Urine ACR in 3 months to monitor GFR trajectory.", "Schedule an ultrasound scan of the kidneys to check for structural changes or scarring.", "Maintain an active log of clinical vitals for review at the next outpatient clinic visit."]}	1	2026-05-22 18:41:07.70015
2	3	1.2	150	45	Female	120	1.02	1	0	normal	40	138	4.2	14.5	8000	no	no	56.89	G3a	A2	High	High risk of CKD progression. Refer to nephrology if not already under specialist care. Intensify blood pressure and glycaemic control. Monitor eGFR and ACR every 3–4 months. Evaluate for complications (anaemia, bone disease, acidosis).	CKD Detected	1	{"medical_insights": "Based on the Decision Tree model trained on the UCI CKD dataset, the patient is classified as 'CKD Detected' with a confidence of 100%.  Serum Creatinine (1.2 mg/dL) is elevated above normal gender thresholds, pointing towards reduced glomerular filtration.", "risk_analysis": "Risk analysis suggests active kidney damage or impaired filtration function. The presence of risk factors needs urgent monitoring to prevent progressive loss of nephrons.", "suggested_precautions": ["Review all prescriptions; avoid nephrotoxic drugs, especially NSAIDs (e.g., ibuprofen, naproxen).", "Ensure adequate hydration, matching fluid intake with output levels.", "Consult a nephrologist if GFR drops below 30 mL/min/1.73 m\\u00b2."], "lifestyle_recommendations": ["Maintain low-sodium dietary habits to protect baseline vascular pressure.", "Engage in moderate physical activity for 30 minutes, 5 days a week.", "Cease smoking immediately, as nicotine accelerates renal microvascular deterioration.", "Limit high-protein diets; target moderate intake (0.8 g/kg body weight) to reduce glomerular load."], "follow_up_recommendations": ["Re-check Serum Creatinine and Urine ACR in 3 months to monitor GFR trajectory.", "Schedule an ultrasound scan of the kidneys to check for structural changes or scarring.", "Maintain an active log of clinical vitals for review at the next outpatient clinic visit."]}	1	2026-05-22 19:40:40.159995
\.


--
-- Data for Name: patients; Type: TABLE DATA; Schema: public; Owner: sambomatic
--

COPY public.patients (id, patient_id, first_name, last_name, age, gender, phone, created_at, created_by) FROM stdin;
1	PT-9988	Jane	Smith	45	Female	jane@example.com	2026-05-22 18:29:27.982565	1
2	PT-4117	Usman	Abubakar Sambo	25	Male	1234567890	2026-05-22 19:15:41.223321	1
3	PT-9838	Jane	Smith	45	Female	jane@example.com	2026-05-22 19:26:42.767621	1
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: sambomatic
--

COPY public.users (id, username, password_hash, full_name, created_at) FROM stdin;
1	admin	scrypt:32768:8:1$Ufe31dv7g9XICuC4$41110b8c06b9be95847803740301f89e7d3bd3d99bccc369f2fc51ce980fcb4ddf2f7d2888d6055fda82e4dbb7560ea3806c62872e481745c7aea85abb28383a	Administrator	2026-05-22 18:20:51.107581
\.


--
-- Name: diagnoses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: sambomatic
--

SELECT pg_catalog.setval('public.diagnoses_id_seq', 2, true);


--
-- Name: patients_id_seq; Type: SEQUENCE SET; Schema: public; Owner: sambomatic
--

SELECT pg_catalog.setval('public.patients_id_seq', 3, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: sambomatic
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: diagnoses diagnoses_pkey; Type: CONSTRAINT; Schema: public; Owner: sambomatic
--

ALTER TABLE ONLY public.diagnoses
    ADD CONSTRAINT diagnoses_pkey PRIMARY KEY (id);


--
-- Name: patients patients_pkey; Type: CONSTRAINT; Schema: public; Owner: sambomatic
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT patients_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: sambomatic
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_patients_patient_id; Type: INDEX; Schema: public; Owner: sambomatic
--

CREATE UNIQUE INDEX ix_patients_patient_id ON public.patients USING btree (patient_id);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: sambomatic
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: diagnoses diagnoses_diagnosed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: sambomatic
--

ALTER TABLE ONLY public.diagnoses
    ADD CONSTRAINT diagnoses_diagnosed_by_fkey FOREIGN KEY (diagnosed_by) REFERENCES public.users(id);


--
-- Name: diagnoses diagnoses_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: sambomatic
--

ALTER TABLE ONLY public.diagnoses
    ADD CONSTRAINT diagnoses_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: patients patients_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: sambomatic
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT patients_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

\unrestrict 1edMWlM0T4foK3FgHsed58xntoY0oaGVE3Q8x6ELxq5aQur5sWFVu0Xgeb1ENzP

