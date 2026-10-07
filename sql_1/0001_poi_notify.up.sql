-- SPDX-FileCopyrightText: Tim Sutton
-- SPDX-License-Identifier: MIT
--
-- 0001 · poi change notifications for QGIS auto-refresh (UP)
--
-- QGIS's PostgreSQL provider only ever issues `LISTEN qgis` (verified in the
-- provider binary: the SQL literal is `LISTEN qgis`). It therefore ignores any
-- other channel. The *payload* is what QGIS matches against a layer's
-- `setRefreshOnNotifyMessage(...)` filter.
--
-- So: emit on channel 'qgis' with payload 'poi'. A statement-level trigger
-- keeps this to one notification per statement (a 1000-row bulk insert fires
-- once, not 1000 times). TRUNCATE is included so a table wipe also refreshes.
--
-- Apply:  pg psql -f sql/0001_poi_notify.up.sql
-- Revert: pg psql -f sql/0001_poi_notify.down.sql

BEGIN;

CREATE OR REPLACE FUNCTION public.notify_poi_change()
  RETURNS trigger
  LANGUAGE plpgsql
AS $function$
BEGIN
  -- Channel MUST be 'qgis' (hardcoded LISTEN in the QGIS provider).
  -- Payload 'poi' is matched by the layer's refresh-on-notify message.
  PERFORM pg_notify('qgis', 'poi');
  RETURN NULL;
END;
$function$;

CREATE OR REPLACE TRIGGER poi_change_notify
  AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON public.poi
  FOR EACH STATEMENT
  EXECUTE FUNCTION public.notify_poi_change();

COMMIT;
