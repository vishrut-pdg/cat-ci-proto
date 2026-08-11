FROM postgres:17.10-alpine3.24

COPY init/001_seed.sql.gz /docker-entrypoint-initdb.d/001_seed.sql.gz

EXPOSE 5432
