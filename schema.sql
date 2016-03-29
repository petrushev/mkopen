SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';

SET search_path = public, pg_catalog;

CREATE FUNCTION b642uuid(id text) RETURNS uuid
    LANGUAGE sql IMMUTABLE
    AS $$
     select
       encode(
         decode(replace(id||'==', '_','/'),
                'base64'),
         'hex')::uuid
$$;

CREATE FUNCTION join_text_array(text[], text) RETURNS text
    LANGUAGE sql IMMUTABLE
    AS $_$SELECT array_to_string($1, $2)$_$;

CREATE FUNCTION uuid2b64(id uuid) RETURNS text
    LANGUAGE sql IMMUTABLE
    AS $$
     select   replace(replace( encode(decode(
     replace(id::text, '-', ''),
      'hex'),'base64'),'/','_'), '==','')
$$;

SET default_with_oids = false;

CREATE TABLE data (
    id uuid NOT NULL,
    last_checked date NOT NULL,
    catalog_id text[] NOT NULL,
    CONSTRAINT ck_data_catalog_id_uuid CHECK (((encode(digest((array_to_string(catalog_id, '/'::text))::bytea, 'md5'::text), 'hex'::text))::uuid = id))
);

CREATE TABLE version (
    id uuid NOT NULL,
    data bytea NOT NULL,
    updated date NOT NULL,
    data_id uuid NOT NULL,
    metadata json DEFAULT '{}'::json NOT NULL,
    CONSTRAINT ck_version_uuid_id CHECK (((encode(digest(data, 'md5'::text), 'hex'::text))::uuid = id))
);

ALTER TABLE ONLY data
    ADD CONSTRAINT p_data PRIMARY KEY (id);

ALTER TABLE ONLY version
    ADD CONSTRAINT p_version PRIMARY KEY (id);

ALTER TABLE ONLY version
    ADD CONSTRAINT u_version UNIQUE (updated, data_id);

CREATE INDEX fki_version_data ON version USING btree (data_id);

CREATE INDEX i3_data_catalog ON data USING gist (join_text_array(catalog_id, ' '::text) gist_trgm_ops);

CREATE INDEX i_data_catalog ON data USING gin (catalog_id);

ALTER TABLE ONLY version
    ADD CONSTRAINT fk_version_data FOREIGN KEY (data_id) REFERENCES data(id) ON UPDATE CASCADE ON DELETE RESTRICT;

