-- SPDX-FileCopyrightText: Tim Sutton
-- SPDX-License-Identifier: MIT
--
-- 0002 · auto-populated updated_at on poi (DOWN)
--
-- Reverts 0002_poi_updated_at.up.sql: drops the BEFORE trigger, its function,
-- and the updated_at column.

BEGIN;

DROP TRIGGER IF EXISTS poi_set_updated_at ON public.poi;
DROP FUNCTION IF EXISTS public.poi_set_updated_at();
ALTER TABLE public.poi DROP COLUMN IF EXISTS updated_at;

COMMIT;
