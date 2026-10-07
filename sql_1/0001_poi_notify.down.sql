-- SPDX-FileCopyrightText: Tim Sutton
-- SPDX-License-Identifier: MIT
--
-- 0001 · poi change notifications for QGIS auto-refresh (DOWN)
--
-- Reverts 0001_poi_notify.up.sql, restoring the original pre-fix behaviour:
-- an empty payload on the (QGIS-invisible) 'poi_changes' channel, and the
-- trigger without TRUNCATE coverage. This makes the migration reversible.

BEGIN;

CREATE OR REPLACE FUNCTION public.notify_poi_change()
  RETURNS trigger
  LANGUAGE plpgsql
AS $function$
BEGIN
  PERFORM pg_notify('poi_changes', '');
  RETURN NULL;
END;
$function$;

CREATE OR REPLACE TRIGGER poi_change_notify
  AFTER INSERT OR UPDATE OR DELETE ON public.poi
  FOR EACH STATEMENT
  EXECUTE FUNCTION public.notify_poi_change();

COMMIT;
