--
-- PostgreSQL database dump
--

-- Dumped from database version 15.4
-- Dumped by pg_dump version 17.5

-- Started on 2025-10-18 20:54:01 PDT

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
SET row_security = on;

DROP DATABASE IF EXISTS investment_db;
--
-- TOC entry 3684 (class 1262 OID 17707)
-- Name: investment_db; Type: DATABASE; Schema: -; Owner: postgres
--

CREATE DATABASE investment_db WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'C';

-- Role: postgres
-- DROP ROLE IF EXISTS postgres;

ALTER DATABASE investment_db OWNER TO postgres;

\connect investment_db

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
SET row_security = on;

--
-- TOC entry 4 (class 2615 OID 2200)
-- Name: public; Type: SCHEMA; Schema: -; Owner: pg_database_owner
--

CREATE SCHEMA public;


ALTER SCHEMA public OWNER TO pg_database_owner;

--
-- TOC entry 3685 (class 0 OID 0)
-- Dependencies: 4
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: pg_database_owner
--

COMMENT ON SCHEMA public IS 'standard public schema';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 221 (class 1259 OID 18181)
-- Name: company_valuations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.company_valuations (
    company_valuation_id bigint NOT NULL,
    as_of_date date NOT NULL,
    price_source character varying(50) DEFAULT 'External'::character varying NOT NULL,
    company character varying(255),
    sector_subsector character varying(255),
    price numeric(15,2),
    price_change_amt numeric(15,2),
    price_change_perc numeric(8,4),
    last_matched_price character varying(50),
    share_class character varying(100),
    post_money_valuation character varying(50),
    price_per_share numeric(15,2),
    amount_raised character varying(50),
    raw_data_json jsonb,
    created_ts timestamp with time zone DEFAULT now(),
    last_updated_ts timestamp with time zone DEFAULT now()
);


ALTER TABLE public.company_valuations OWNER TO postgres;

--
-- TOC entry 3686 (class 0 OID 0)
-- Dependencies: 221
-- Name: TABLE company_valuations; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.company_valuations IS 'Company pricing and valuation data from various external sources';


--
-- TOC entry 3687 (class 0 OID 0)
-- Dependencies: 221
-- Name: COLUMN company_valuations.as_of_date; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.company_valuations.as_of_date IS 'Date when the pricing data was captured';


--
-- TOC entry 3688 (class 0 OID 0)
-- Dependencies: 221
-- Name: COLUMN company_valuations.price_source; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.company_valuations.price_source IS 'Source of the pricing data (e.g., ForgeGlobal, PitchBook, etc.)';


--
-- TOC entry 3689 (class 0 OID 0)
-- Dependencies: 221
-- Name: COLUMN company_valuations.price; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.company_valuations.price IS 'Current price extracted from composite price field';


--
-- TOC entry 3690 (class 0 OID 0)
-- Dependencies: 221
-- Name: COLUMN company_valuations.price_change_amt; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.company_valuations.price_change_amt IS 'Price change amount extracted from price data';


--
-- TOC entry 3691 (class 0 OID 0)
-- Dependencies: 221
-- Name: COLUMN company_valuations.price_change_perc; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.company_valuations.price_change_perc IS 'Price change percentage extracted from price data';


--
-- TOC entry 3692 (class 0 OID 0)
-- Dependencies: 221
-- Name: COLUMN company_valuations.post_money_valuation; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.company_valuations.post_money_valuation IS 'Post-money valuation (cleaned from Post-Money Valuation2)';


--
-- TOC entry 3693 (class 0 OID 0)
-- Dependencies: 221
-- Name: COLUMN company_valuations.raw_data_json; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.company_valuations.raw_data_json IS 'Complete raw CSV row data for future parsing if needed';


--
-- TOC entry 217 (class 1259 OID 17959)
-- Name: external_platform_dtl; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.external_platform_dtl (
    external_platform_id bigint NOT NULL,
    name text NOT NULL,
    created_ts timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_updated_ts timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    platform_type text DEFAULT 'Trading Platform'::text NOT NULL
);


ALTER TABLE public.external_platform_dtl OWNER TO postgres;

--
-- TOC entry 214 (class 1259 OID 17930)
-- Name: holding_dtl; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.holding_dtl (
    holding_id bigint NOT NULL,
    holding_dt date NOT NULL,
    portfolio_id bigint NOT NULL,
    security_id bigint NOT NULL,
    quantity double precision NOT NULL,
    price double precision NOT NULL,
    market_value double precision NOT NULL,
    created_ts timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_updated_ts timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    avg_price double precision,
    security_price_dt date,
    holding_cost_amt double precision,
    unreal_gain_loss_amt double precision,
    unreal_gain_loss_perc double precision
);


ALTER TABLE public.holding_dtl OWNER TO postgres;

--
-- TOC entry 215 (class 1259 OID 17936)
-- Name: portfolio_dtl; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.portfolio_dtl (
    portfolio_id bigint NOT NULL,
    user_id bigint NOT NULL,
    name text NOT NULL,
    open_date date NOT NULL,
    close_date date,
    created_ts timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_updated_ts timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.portfolio_dtl OWNER TO postgres;

--
-- TOC entry 216 (class 1259 OID 17943)
-- Name: security_dtl; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.security_dtl (
    security_id bigint NOT NULL,
    ticker text NOT NULL,
    name text NOT NULL,
    company_name text NOT NULL,
    security_currency character varying(10) DEFAULT 'USD'::text NOT NULL,
    created_ts timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_updated_ts timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_private boolean DEFAULT false
);


ALTER TABLE public.security_dtl OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 18142)
-- Name: security_price_dtl; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.security_price_dtl (
    security_price_id bigint NOT NULL,
    security_id bigint NOT NULL,
    price_source_id bigint NOT NULL,
    price_date date NOT NULL,
    price double precision NOT NULL,
    market_cap double precision,
    price_currency text DEFAULT 'USD'::text NOT NULL,
    addl_notes text,
    created_ts timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_updated_ts timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.security_price_dtl OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 17996)
-- Name: transaction_dtl; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transaction_dtl (
    transaction_id bigint NOT NULL,
    portfolio_id bigint NOT NULL,
    security_id bigint NOT NULL,
    external_platform_id bigint NOT NULL,
    transaction_date date NOT NULL,
    transaction_type text NOT NULL,
    transaction_qty double precision NOT NULL,
    transaction_price double precision NOT NULL,
    transaction_fee double precision DEFAULT 0.0 NOT NULL,
    transaction_fee_percent double precision DEFAULT 0.0 NOT NULL,
    carry_fee double precision DEFAULT 0.0 NOT NULL,
    carry_fee_percent double precision DEFAULT 0.0 NOT NULL,
    management_fee double precision DEFAULT 0.0 NOT NULL,
    management_fee_percent double precision DEFAULT 0.0 NOT NULL,
    external_manager_fee double precision DEFAULT 0.0 NOT NULL,
    external_manager_fee_percent double precision DEFAULT 0.0 NOT NULL,
    created_ts timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_updated_ts timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    total_inv_amt double precision DEFAULT 0.0,
    total_inv_amt_net_of_fees double precision DEFAULT 0.0,
    rel_transaction_id bigint
);


ALTER TABLE public.transaction_dtl OWNER TO postgres;

--
-- TOC entry 218 (class 1259 OID 17981)
-- Name: user_dtl; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_dtl (
    user_id bigint NOT NULL,
    first_name text NOT NULL,
    last_name text NOT NULL,
    email text,
    password_hash text,
    created_ts timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_updated_ts timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_admin boolean DEFAULT false
);


ALTER TABLE public.user_dtl OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 26352)
-- Name: v_transaction_full; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_transaction_full AS
 SELECT t.transaction_id,
    t.portfolio_id,
    pf.name AS portfolio_name,
    pf.user_id,
    ((COALESCE(u.first_name, ''::text) ||
        CASE
            WHEN ((u.first_name IS NOT NULL) AND (u.last_name IS NOT NULL)) THEN ' '::text
            ELSE ''::text
        END) || COALESCE(u.last_name, ''::text)) AS user_full_name,
    t.security_id,
    s.ticker AS security_ticker,
    s.name AS security_name,
    t.external_platform_id,
    tp.name AS external_platform_name,
    t.transaction_date,
    t.transaction_type,
    t.transaction_qty,
    t.transaction_price,
    t.transaction_fee,
    t.transaction_fee_percent,
    t.carry_fee,
    t.carry_fee_percent,
    t.management_fee,
    t.management_fee_percent,
    t.external_manager_fee,
    t.external_manager_fee_percent,
    (t.transaction_qty * t.transaction_price) AS gross_amount,
    t.total_inv_amt,
    (((COALESCE(t.transaction_fee, (0)::double precision) + COALESCE(t.carry_fee, (0)::double precision)) + COALESCE(t.management_fee, (0)::double precision)) + COALESCE(t.external_manager_fee, (0)::double precision)) AS total_fee,
    ((t.transaction_qty * t.transaction_price) - (((COALESCE(t.transaction_fee, (0)::double precision) + COALESCE(t.carry_fee, (0)::double precision)) + COALESCE(t.management_fee, (0)::double precision)) + COALESCE(t.external_manager_fee, (0)::double precision))) AS net_amount,
    t.rel_transaction_id,
    t.created_ts,
    t.last_updated_ts
   FROM ((((public.transaction_dtl t
     LEFT JOIN public.portfolio_dtl pf ON ((pf.portfolio_id = t.portfolio_id)))
     LEFT JOIN public.user_dtl u ON ((u.user_id = pf.user_id)))
     LEFT JOIN public.security_dtl s ON ((s.security_id = t.security_id)))
     LEFT JOIN public.external_platform_dtl tp ON ((tp.external_platform_id = t.external_platform_id)));


ALTER VIEW public.v_transaction_full OWNER TO postgres;

--
-- TOC entry 3678 (class 0 OID 18181)
-- Dependencies: 221
-- Data for Name: company_valuations; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 3674 (class 0 OID 17959)
-- Dependencies: 217
-- Data for Name: external_platform_dtl; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 3671 (class 0 OID 17930)
-- Dependencies: 214
-- Data for Name: holding_dtl; Type: TABLE DATA; Schema: public; Owner: postgres
--

--
-- TOC entry 3672 (class 0 OID 17936)
-- Dependencies: 215
-- Data for Name: portfolio_dtl; Type: TABLE DATA; Schema: public; Owner: postgres
--


--
-- TOC entry 3673 (class 0 OID 17943)
-- Dependencies: 216
-- Data for Name: security_dtl; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1760072813777906, 'VOO', 'Vanguard S&P 500 ETF', 'Vanguard', 'USD', '2025-10-09 22:06:53.777921', '2025-10-09 22:06:53.777923', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1760239586823526, '021ESC017', 'ALTABA INC XXXESC PEND POSS FUTR DISTR', 'ALTABA INC XXXESC PEND POSS FUTR DISTR', 'USD', '2025-10-11 20:26:26.823551', '2025-10-11 20:26:26.823553', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759720693582666, 'AVLV', 'AVANTIS U S LARGE CAP VALUE ETF', 'AVANTIS U S LARGE CAP VALUE ETF', 'USD', '2025-10-05 20:18:13.582672', '2025-10-11 20:26:26.833976', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759717325351498, 'BA', 'BOEING CO', 'BOEING CO', 'USD', '2025-10-05 19:22:05.351507', '2025-10-11 20:26:26.840093', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759717325381067, 'BAC', 'BANK OF AMERICA CORP', 'BANK OF AMERICA CORP', 'USD', '2025-10-05 19:22:05.381071', '2025-10-11 20:26:26.841611', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759717325399894, 'C', 'CITIGROUP INC', 'CITIGROUP INC', 'USD', '2025-10-05 19:22:05.399897', '2025-10-11 20:26:26.84262', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759717325445954, 'CRM', 'SALESFORCE INC', 'SALESFORCE INC', 'USD', '2025-10-05 19:22:05.445959', '2025-10-11 20:26:26.843888', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1757479692542044, 'CHAIN', 'Chain', 'Chain', 'USD', '2025-09-09 21:48:12.542057', '2025-10-11 20:26:26.895487', true) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1757479692574804, 'IMPOSSIBLE', 'Impossible Foods', 'Impossible Foods', 'USD', '2025-09-09 21:48:12.574812', '2025-10-11 20:26:26.896274', true) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759643277804245, 'DATABRICKS', 'Databricks III', 'Databrics, Inc.', 'USD', '2025-10-04 22:47:57.804271', '2025-10-05 00:40:50.295811', true) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759180552808257, 'Polymarket II', 'Polymarket II', 'Polymarket', 'USD', '2025-09-29 14:15:52.808285', '2025-10-05 00:41:43.41369', true) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759717325426093, 'CVX', 'Chevron', 'Chevron', 'USD', '2025-10-05 19:22:05.426098', '2025-10-05 19:22:05.426099', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759720377733114, 'GOOG', 'Google Inc - Class C', 'Google Inc - Class C', 'USD', '2025-10-05 20:12:57.73313', '2025-10-05 20:12:57.733134', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759720377747606, 'GOOGL', 'Google Inc - Class A', 'Google Inc - Class A', 'USD', '2025-10-05 20:12:57.747647', '2025-10-05 20:12:57.747653', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759720693548754, 'DIDIY', 'DIDI GLOBAL INC FUNSPONS', 'DIDI GLOBAL INC FUNSPONS', 'USD', '2025-10-05 20:18:13.548764', '2025-10-11 20:26:26.851052', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759720693538655, 'DOCU', 'DOCUSIGN INC', 'DOCUSIGN INC', 'USD', '2025-10-05 20:18:13.538662', '2025-10-11 20:26:26.853851', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759720693519359, 'EZU', 'ISHARES MSCI EUROZONE ETF', 'ISHARES MSCI EUROZONE ETF', 'USD', '2025-10-05 20:18:13.519366', '2025-10-11 20:26:26.85505', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1760239586856360, 'HES', 'HESS CORP', 'HESS CORP', 'USD', '2025-10-11 20:26:26.856369', '2025-10-11 20:26:26.85637', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759720693510883, 'IAU', 'ISHARES GOLD ETF', 'ISHARES GOLD ETF', 'USD', '2025-10-05 20:18:13.510894', '2025-10-11 20:26:26.85702', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759720693557455, 'INVZ', 'INNOVIZ TECHNOLOGIES L F', 'INNOVIZ TECHNOLOGIES L F', 'USD', '2025-10-05 20:18:13.557464', '2025-10-11 20:26:26.858771', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759720693574762, 'IUSG', 'ISHARES CORE S&P US GROWTH ETF', 'ISHARES CORE S&P US GROWTH ETF', 'USD', '2025-10-05 20:18:13.574767', '2025-10-11 20:26:26.861875', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759720377759663, 'LMND', 'LEMONADE INC', 'LEMONADE INC', 'USD', '2025-10-05 20:12:57.75967', '2025-10-11 20:26:26.864081', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1757479692561265, 'LYFT', 'LYFT INC CLASS A', 'LYFT INC CLASS A', 'USD', '2025-09-09 21:48:12.561279', '2025-10-11 20:26:26.865328', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759717325435119, 'LYG', 'LLOYDS BANKING GROUP FSPONSORED ADR 1 ADR REPS 4 ORD SHS', 'LLOYDS BANKING GROUP FSPONSORED ADR 1 ADR REPS 4 ORD SHS', 'USD', '2025-10-05 19:22:05.435128', '2025-10-11 20:26:26.866508', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759717325371213, 'MAGS', 'LISTED FNDS RONDHL MGNFCNT ETF', 'LISTED FNDS RONDHL MGNFCNT ETF', 'USD', '2025-10-05 19:22:05.371218', '2025-10-11 20:26:26.867777', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1760239586870092, 'ME', '23ANDME HOLDING CO FCLASS A', '23ANDME HOLDING CO FCLASS A', 'USD', '2025-10-11 20:26:26.870101', '2025-10-11 20:26:26.870101', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759720693565887, 'MEHCQ', 'CHROME HLDG CO CLASS A', 'CHROME HLDG CO CLASS A', 'USD', '2025-10-05 20:18:13.565894', '2025-10-11 20:26:26.870655', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1757479692452033, 'MELI', 'MERCADOLIBRE INC', 'MERCADOLIBRE INC', 'USD', '2025-09-09 21:48:12.452047', '2025-10-11 20:26:26.871474', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1760239586872092, 'MSFT', 'MICROSOFT CORP', 'MICROSOFT CORP', 'USD', '2025-10-11 20:26:26.872099', '2025-10-11 20:26:26.8721', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1757479692503706, 'NVDA', 'NVIDIA CORP', 'NVIDIA CORP', 'USD', '2025-09-09 21:48:12.503717', '2025-10-11 20:26:26.872433', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1757479692552060, 'PINS', 'PINTEREST INC CLASS A', 'PINTEREST INC CLASS A', 'USD', '2025-09-09 21:48:12.552071', '2025-10-11 20:26:26.880929', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1757479692514984, 'PLTR', 'PALANTIR TECHNOLOGIES INC', 'PALANTIR TECHNOLOGIES INC', 'USD', '2025-09-09 21:48:12.514994', '2025-10-11 20:26:26.882799', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759720693497020, 'SKYY', 'FIRST TRUST CLOUD COMPUTING ETF', 'FIRST TRUST CLOUD COMPUTING ETF', 'USD', '2025-10-05 20:18:13.497034', '2025-10-11 20:26:26.885312', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1760239586886426, 'SPLK', 'TDA TRAN - Sold ...125 (SPLK) @157.0000', 'TDA TRAN - Sold ...125 (SPLK) @157.0000', 'USD', '2025-10-11 20:26:26.886434', '2025-10-11 20:26:26.886435', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759717325417601, 'TMUS', 'T-MOBILE US INC', 'T-MOBILE US INC', 'USD', '2025-10-05 19:22:05.417604', '2025-10-11 20:26:26.886912', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759717325453700, 'TTD', 'THE TRADE DESK INC CLASS A', 'THE TRADE DESK INC CLASS A', 'USD', '2025-10-05 19:22:05.453702', '2025-10-11 20:26:26.887815', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759720693528075, 'TTWO', 'TAKE-TWO INTERACTIVE SOF', 'TAKE-TWO INTERACTIVE SOF', 'USD', '2025-10-05 20:18:13.528082', '2025-10-11 20:26:26.888475', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759717325409584, 'UAL', 'UNITED AIRLINES HLDGS', 'UNITED AIRLINES HLDGS', 'USD', '2025-10-05 19:22:05.409587', '2025-10-11 20:26:26.889188', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759717325390870, 'WFC', 'WELLS FARGO & CO', 'WELLS FARGO & CO', 'USD', '2025-10-05 19:22:05.390873', '2025-10-11 20:26:26.891486', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1759717325360370, 'XLP', 'SPDR FUND CONSUMER STAPLES ETF', 'SPDR FUND CONSUMER STAPLES ETF', 'USD', '2025-10-05 19:22:05.360376', '2025-10-11 20:26:26.892205', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1757479692568350, 'ZS', 'ZSCALER INC', 'ZSCALER INC', 'USD', '2025-09-09 21:48:12.568358', '2025-10-11 20:26:26.892854', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1757479692524256, 'BETTERMENT', 'Betterment', 'Betterment', 'USD', '2025-09-09 21:48:12.524271', '2025-10-11 20:26:26.893533', true) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1757479692533617, 'BAREFOOT', 'Barefoot Networks', 'Barefoot Networks', 'USD', '2025-09-09 21:48:12.533627', '2025-10-11 20:26:26.894377', true) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1757479692583146, 'KLAR', 'Klarna', 'Klarna', 'USD', '2025-09-09 21:48:12.583157', '2025-10-11 20:26:26.897148', false) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1757479692589624, 'AUTOANY', 'Automation Anywhere', 'Automation Anywhere', 'USD', '2025-09-09 21:48:12.589633', '2025-10-11 20:26:26.898224', true) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1757479692597883, 'ANTHROPIC', 'Anthrtopic', 'Anthrtopic', 'USD', '2025-09-09 21:48:12.597892', '2025-10-11 20:26:26.899303', true) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1757479692604924, 'OPENAI', 'OpenAI', 'OpenAI', 'USD', '2025-09-09 21:48:12.604934', '2025-10-11 20:26:26.900148', true) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1757479692618025, 'NEURALINK', 'Neuralink', 'Neuralink', 'USD', '2025-09-09 21:48:12.618037', '2025-10-11 20:26:26.900877', true) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1757479692625826, 'GROQ', 'Groq', 'Groq', 'USD', '2025-09-09 21:48:12.62584', '2025-10-11 20:26:26.901504', true) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1757479692632487, 'SPACEX', 'SpaceX', 'SpaceX', 'USD', '2025-09-09 21:48:12.632496', '2025-10-11 20:26:26.902105', true) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1757479692638018, 'ANDURIL', 'Anduril', 'Anduril', 'USD', '2025-09-09 21:48:12.638026', '2025-10-11 20:26:26.902832', true) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1757479692644324, 'XAI', 'xAI', 'xAI', 'USD', '2025-09-09 21:48:12.644334', '2025-10-11 20:26:26.903624', true) ON CONFLICT DO NOTHING;
INSERT INTO public.security_dtl (security_id, ticker, name, company_name, security_currency, created_ts, last_updated_ts, is_private) VALUES (1757479692650786, 'PERPLEXITY', 'Perplexity', 'Perplexity', 'USD', '2025-09-09 21:48:12.650793', '2025-10-11 20:26:26.904237', true) ON CONFLICT DO NOTHING;


--
-- TOC entry 3677 (class 0 OID 18142)
-- Dependencies: 220
-- Data for Name: security_price_dtl; Type: TABLE DATA; Schema: public; Owner: postgres
--


--
-- TOC entry 3676 (class 0 OID 17996)
-- Dependencies: 219
-- Data for Name: transaction_dtl; Type: TABLE DATA; Schema: public; Owner: postgres
--


--
-- TOC entry 3675 (class 0 OID 17981)
-- Dependencies: 218
-- Data for Name: user_dtl; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.user_dtl (user_id, first_name, last_name, email, password_hash, created_ts, last_updated_ts, is_admin) VALUES (1757397011827953, 'Srinivas', 'Sunkara Admin', 'test@example.com', 'pbkdf2_sha256$100000$-eOrKDYywm9cnMFdW8Q9zg==$SHbpwTmUdXFL0j1kgUSBFx2fI90kD-L2-0mE5MMQB1M=', '2025-09-08 22:50:11.827968', '2025-09-16 22:22:56.349992', true) ON CONFLICT DO NOTHING;


--
-- TOC entry 3521 (class 2606 OID 18192)
-- Name: company_valuations company_valuations_company_as_of_date_price_source_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.company_valuations
    ADD CONSTRAINT company_valuations_company_as_of_date_price_source_key UNIQUE (company, as_of_date, price_source);


--
-- TOC entry 3523 (class 2606 OID 18190)
-- Name: company_valuations company_valuations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.company_valuations
    ADD CONSTRAINT company_valuations_pkey PRIMARY KEY (company_valuation_id);


--
-- TOC entry 3503 (class 2606 OID 18034)
-- Name: holding_dtl holding_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.holding_dtl
    ADD CONSTRAINT holding_pkey PRIMARY KEY (holding_id);


--
-- TOC entry 3505 (class 2606 OID 18048)
-- Name: portfolio_dtl portfolio_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.portfolio_dtl
    ADD CONSTRAINT portfolio_pkey PRIMARY KEY (portfolio_id);


--
-- TOC entry 3507 (class 2606 OID 18062)
-- Name: security_dtl security_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.security_dtl
    ADD CONSTRAINT security_pkey PRIMARY KEY (security_id);


--
-- TOC entry 3517 (class 2606 OID 18151)
-- Name: security_price_dtl security_price_dtl_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.security_price_dtl
    ADD CONSTRAINT security_price_dtl_pkey PRIMARY KEY (security_price_id);


--
-- TOC entry 3511 (class 2606 OID 18084)
-- Name: external_platform_dtl tradingplatform_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.external_platform_dtl
    ADD CONSTRAINT tradingplatform_pkey PRIMARY KEY (external_platform_id);


--
-- TOC entry 3515 (class 2606 OID 18092)
-- Name: transaction_dtl transaction_dtl_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transaction_dtl
    ADD CONSTRAINT transaction_dtl_pkey PRIMARY KEY (transaction_id);


--
-- TOC entry 3519 (class 2606 OID 26360)
-- Name: security_price_dtl unique_sec_price_by_source; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.security_price_dtl
    ADD CONSTRAINT unique_sec_price_by_source UNIQUE (security_id, price_source_id, price_date);


--
-- TOC entry 3509 (class 2606 OID 26362)
-- Name: security_dtl unique_ticker_constraint; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.security_dtl
    ADD CONSTRAINT unique_ticker_constraint UNIQUE (ticker);


--
-- TOC entry 3513 (class 2606 OID 18119)
-- Name: user_dtl user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_dtl
    ADD CONSTRAINT user_pkey PRIMARY KEY (user_id);


--
-- TOC entry 3524 (class 1259 OID 18193)
-- Name: idx_company_valuations_as_of_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_company_valuations_as_of_date ON public.company_valuations USING btree (as_of_date);


--
-- TOC entry 3525 (class 1259 OID 18194)
-- Name: idx_company_valuations_company; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_company_valuations_company ON public.company_valuations USING btree (company);


--
-- TOC entry 3526 (class 1259 OID 18196)
-- Name: idx_company_valuations_price_source; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_company_valuations_price_source ON public.company_valuations USING btree (price_source);


--
-- TOC entry 3527 (class 1259 OID 18195)
-- Name: idx_company_valuations_sector; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_company_valuations_sector ON public.company_valuations USING btree (sector_subsector);


-- Completed on 2025-10-18 20:54:01 PDT

--
-- PostgreSQL database dump complete
--

