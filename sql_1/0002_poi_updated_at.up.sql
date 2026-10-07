-- SPDX-FileCopyrightText: Tim Sutton
-- SPDX-License-Identifier: MIT
--
-- 0002 · auto-populated updated_at on poi (UP)
--
-- Adds a timestamp column that defaults to now() on insert and is refreshed on
-- every update by a BEFORE row trigger. Independent of the NOTIFY wiring in
-- 0001 (that trigger is AFTER STATEMENT; this one is BEFORE ROW).
--
-- Apply:  pg psql -f sql/0002_poi_updated_at.up.sql
-- Revert: pg psql -f sql/0002_poi_updated_at.down.sql

BEGIN;

ALTER TABLE public.poi
  ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

CREATE OR REPLACE FUNCTION public.poi_set_updated_at()
  RETURNS trigger
  LANGUAGE plpgsql
AS $function$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$function$;

CREATE OR REPLACE TRIGGER poi_set_updated_at
  BEFORE INSERT OR UPDATE ON public.poi
  FOR EACH ROW
  EXECUTE FUNCTION public.poi_set_updated_at();

COMMIT;
