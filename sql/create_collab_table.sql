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
