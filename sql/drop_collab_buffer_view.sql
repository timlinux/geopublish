-- SPDX-FileCopyrightText: 2026 Kartoza
-- SPDX-License-Identifier: MIT
-- Reverts create_collab_buffer_view.sql: drops the view and restores
-- notify_collab_change() to the single-payload version from
-- create_collab_table.sql. Does not touch collab itself.
DROP VIEW IF EXISTS public.collab_buffer_100km;

CREATE OR REPLACE FUNCTION public.notify_collab_change()
  RETURNS trigger
  LANGUAGE plpgsql
AS $function$
BEGIN
  PERFORM pg_notify('qgis', 'collab');
  RETURN NULL;
END;
$function$;
