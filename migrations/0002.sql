ALTER TABLE spots ADD COLUMN document TEXT;
ALTER TABLE route_spots ADD COLUMN access_confidence TEXT NOT NULL DEFAULT 'proximity-only';
