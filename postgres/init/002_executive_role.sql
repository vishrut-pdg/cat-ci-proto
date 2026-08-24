BEGIN;

INSERT INTO identity_data.roles (id, code, name)
VALUES ('ROLE-EXEC', 'EXECUTIVE', 'Executive')
ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO identity_data.users (
    id, employee_id, first_name, last_name, email,
    department, location, active
)
VALUES (
    'USER-031', 'E10031', 'Robert', 'Miller',
    'robert.miller@example.local', 'Executive Leadership', 'USA', true
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO identity_data.user_roles (user_id, role_id)
SELECT 'USER-031', id
FROM identity_data.roles
WHERE code = 'EXECUTIVE'
ON CONFLICT DO NOTHING;

COMMIT;
