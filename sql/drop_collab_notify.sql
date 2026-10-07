-- SPDX-FileCopyrightText: 2026 Kartoza
-- SPDX-License-Identifier: MIT
-- Reverts the NOTIFY wiring added by create_collab_table.sql, without
-- touching the collab table, its data, or its grants.
DROP TRIGGER IF EXISTS collab_change_notify ON public.collab;
DROP FUNCTION IF EXISTS public.notify_collab_change();
