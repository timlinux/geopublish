-- SPDX-FileCopyrightText: 2026 Kartoza
-- SPDX-License-Identifier: MIT
-- Shared "drop a pin with your name" collaboration layer, EPSG:3857.
CREATE TABLE IF NOT EXISTS collab (
    id SERIAL PRIMARY KEY,
    name TEXT,
    geom geometry(Point, 3857)
);

-- Any connected role can add/edit/remove pins, not just the owner.
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE collab TO PUBLIC;
GRANT USAGE, SELECT ON SEQUENCE collab_id_seq TO PUBLIC;

-- Notify QGIS on every CRUD event, so a connected layer can auto-refresh.
-- QGIS's PostgreSQL provider only ever issues `LISTEN qgis` -- that channel
-- name is hardcoded in QGIS itself, not configurable (see sql_1/0001_poi_notify.up.sql
-- for the same fact applied to the workshop's `poi` table). The *payload*
-- ('collab') is what a layer's setRefreshOnNotifyMessage() is matched
-- against, so several notify-enabled tables can share the one channel
-- without triggering each other's refreshes.
--
-- Statement-level (not row-level) so a bulk INSERT/UPDATE/DELETE fires one
-- notification, not one per row. TRUNCATE is included so a table wipe also
-- refreshes connected layers.
CREATE OR REPLACE FUNCTION public.notify_collab_change()
  RETURNS trigger
  LANGUAGE plpgsql
AS $function$
BEGIN
  PERFORM pg_notify('qgis', 'collab');
  RETURN NULL;
END;
$function$;

CREATE OR REPLACE TRIGGER collab_change_notify
  AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON public.collab
  FOR EACH STATEMENT
  EXECUTE FUNCTION public.notify_collab_change();
