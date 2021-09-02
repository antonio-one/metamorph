# Metamorph

```bash
docker run -d \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_HOST_AUTH_METHOD=trust \
  -p 5432:5432 \
  postgres:latest
```

```bash
psql -h localhost -U postgres
```

```sql
postgres=# create database metamorph;
```

```bash
piccolo migrations forwards metamorph
```
