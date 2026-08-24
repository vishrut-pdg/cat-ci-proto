BEGIN;

CREATE TABLE IF NOT EXISTS catalog.equipment_categories (
    id text PRIMARY KEY,
    name text NOT NULL UNIQUE,
    description text NOT NULL
);

INSERT INTO catalog.equipment_categories (id, name, description) VALUES
    ('excavators', 'Excavators', 'Excavators and hydraulic mining shovels'),
    ('motor-graders', 'Motor Graders', 'Motor grader equipment models'),
    ('wheel-loaders', 'Wheel Loaders', 'Wheel loader equipment models'),
    ('dozers', 'Dozers', 'Track-type tractor and dozer models'),
    ('off-highway-trucks', 'Off Highway Trucks', 'Mining and off-highway truck models')
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description;

ALTER TABLE catalog.equipment_models
    ADD COLUMN IF NOT EXISTS category_id text;

UPDATE catalog.equipment_models SET category_id = CASE equipment_family
    WHEN 'Excavator' THEN 'excavators'
    WHEN 'Hydraulic Shovel' THEN 'excavators'
    WHEN 'Motor Grader' THEN 'motor-graders'
    WHEN 'Wheel Loader' THEN 'wheel-loaders'
    WHEN 'Dozer' THEN 'dozers'
    WHEN 'Mining Truck' THEN 'off-highway-trucks'
END;

ALTER TABLE catalog.equipment_models
    ALTER COLUMN category_id SET NOT NULL;

DO $$ BEGIN
    ALTER TABLE catalog.equipment_models
        ADD CONSTRAINT equipment_models_category_id_fkey
        FOREIGN KEY (category_id) REFERENCES catalog.equipment_categories(id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE INDEX IF NOT EXISTS equipment_models_category_id_idx
    ON catalog.equipment_models(category_id);

COMMIT;
