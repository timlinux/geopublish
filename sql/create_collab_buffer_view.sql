-- SPDX-FileCopyrightText: 2026 Kartoza
-- SPDX-License-Identifier: MIT
--
-- A dynamic, dissolved 100km buffer around every collab pin. It's a plain
-- VIEW (not materialized), so it always reflects collab's current rows --
-- there is nothing to refresh or keep in sync.
--
-- collab.geom is EPSG:3857 (Web Mercator), whose unit is metres but whose
-- scale is *not* uniform with latitude -- buffering directly in 3857 with
-- "100000" would give a correct-looking number that is the wrong distance
-- on the ground almost everywhere except the equator. So each point is
-- transformed to EPSG:4326 and cast to `geography` first, which buffers
-- geodesically (a true 100km circle regardless of latitude), then the
-- dissolved result is cast back and transformed to 3857 to match collab.
CREATE OR REPLACE VIEW public.collab_buffer_100km AS
SELECT
  1 AS id,
  ST_Transform(
    ST_Multi(
      ST_Union(
        ST_Buffer(ST_Transform(geom, 4326)::geography, 100000)::geometry
      )
    ),
    3857
  ) AS geom
FROM public.collab;

GRANT SELECT ON public.collab_buffer_100km TO PUBLIC;

-- Views have no change events of their own to trigger on -- this view's
-- only input is collab, so the existing collab_change_notify trigger
-- (see create_collab_table.sql) is extended to also emit a second,
-- independent payload. A QGIS layer built on the view opts in to it with
-- setRefreshOnNotifyMessage('collab_buffer'), separately from the points
-- layer's 'collab' -- both ride the same hardcoded 'qgis' channel.
CREATE OR REPLACE FUNCTION public.notify_collab_change()
  RETURNS trigger
  LANGUAGE plpgsql
AS $function$
BEGIN
  PERFORM pg_notify('qgis', 'collab');
  PERFORM pg_notify('qgis', 'collab_buffer');
  RETURN NULL;
END;
$function$;
