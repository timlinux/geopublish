-- SPDX-FileCopyrightText: Tim Sutton
-- SPDX-License-Identifier: MIT
--
-- replicate_demo.sql — everything needed to reproduce the PG Notification Demo
-- from an empty database. Idempotent: safe to run more than once.
--
--   createdb gis                       # if it does not exist
--   psql -d gis -f sql/replicate_demo.sql
--
-- What it builds:
--   1. PostGIS extension.
--   2. A `poi` table (point geometry) with an auto-populated `updated_at`.
--   3. A BEFORE trigger that stamps `updated_at = now()` on insert and update.
--   4. An AFTER STATEMENT trigger that fires pg_notify('qgis', 'poi') so QGIS
--      auto-refreshes the layer (QGIS hardcodes `LISTEN qgis`; the payload is
--      matched by the layer's setRefreshOnNotifyMessage()).
--   5. A little seed data so a fresh setup shows something.
--
-- QGIS side (Python console, with the poi layer selected):
--   lyr = iface.activeLayer()
--   lyr.setRefreshOnNotifyEnabled(True)
--   lyr.setRefreshOnNotifyMessage('poi')

BEGIN;

-- 1. Spatial support ---------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS postgis;

-- 2. The table ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.poi (
  id         serial PRIMARY KEY,
  geom       geometry(Point, 4326),
  name       text,
  -- Auto-populated: defaults to now() on insert, and the trigger below keeps
  -- it current on every update. NOT NULL because it is always maintained.
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- If the table already existed from an earlier version of the demo, make sure
-- the timestamp column is present.
ALTER TABLE public.poi
  ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

-- Spatial index for map rendering.
CREATE INDEX IF NOT EXISTS sidx_poi_geom ON public.poi USING gist (geom);

-- 3. Keep updated_at current -------------------------------------------------
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

-- 4. Notify QGIS on any change ----------------------------------------------
CREATE OR REPLACE FUNCTION public.notify_poi_change()
  RETURNS trigger
  LANGUAGE plpgsql
AS $function$
BEGIN
  -- Channel MUST be 'qgis' (the QGIS provider hardcodes `LISTEN qgis`).
  -- Payload 'poi' is matched by the layer's refresh-on-notify message.
  PERFORM pg_notify('qgis', 'poi');
  RETURN NULL;
END;
$function$;

CREATE OR REPLACE TRIGGER poi_change_notify
  AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON public.poi
  FOR EACH STATEMENT
  EXECUTE FUNCTION public.notify_poi_change();

-- 5. Seed data (only when the table is empty) --------------------------------
INSERT INTO public.poi (name, geom)
SELECT s.name, ST_SetSRID(ST_MakePoint(s.lon, s.lat), 4326)
FROM (VALUES
  ('Table Mountain', 18.4096, -33.9628),
  ('V&A Waterfront', 18.4197, -33.9030),
  ('Kirstenbosch',   18.4325, -33.9880)
) AS s(name, lon, lat)
WHERE NOT EXISTS (SELECT 1 FROM public.poi);

COMMIT;
