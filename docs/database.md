# Database Setup and Migration Workflow

## Prerequisites

Before proceeding with database operations, ensure:

1. **PostgreSQL is installed and running** on your system
2. **Environment variables are configured** in `.env` file (copy from `.env.example`)
3. **Alembic is initialized** (already done in `alembic/` directory)

## Initial Setup

### 1. Create PostgreSQL Database

```bash
# Using psql (PostgreSQL CLI)
createdb fundlens

# Or using SQL
psql -c "CREATE DATABASE fundlens;"
```

### 2. Configure Environment

Create a `.env` file in the project root with your database connection details:

```env
DATABASE_URL=postgresql://user:password@localhost/fundlens
STAGING_DIR=./uploads/staging
STAGING_TTL_DAYS=7
LOG_LEVEL=INFO
```

### 3. Verify Connection

Test that Alembic can connect to the database:

```bash
alembic current
```

This should return the current database version (initially empty).

## Creating Migrations

### Automatic Migration Generation

After updating your ORM models in `src/models/`, generate a migration automatically:

```bash
alembic revision --autogenerate -m "Description of changes"
```

This creates a new migration file in `alembic/versions/` with:

- SQL schema changes (create tables, add columns, etc.)
- Upgrade function
- Downgrade function

### Manual Migration Creation

If autogenerate doesn't capture all changes, create a blank migration:

```bash
alembic revision -m "Manual migration description"
```

Then edit the generated file in `alembic/versions/` to add the SQL changes.

## Applying Migrations

### Upgrade to Latest Version

```bash
alembic upgrade head
```

This applies all pending migrations to the database.

### Upgrade to Specific Version

```bash
alembic upgrade <revision_id>
```

Example: `alembic upgrade ae1027a6acf`

### Downgrade to Previous Version

```bash
alembic downgrade -1
```

This rolls back one migration. Use `alembic downgrade <revision_id>` to downgrade to a specific version.

## Checking Migration Status

### View Current Database Version

```bash
alembic current
```

### View Migration History

```bash
alembic history --oneline
```

Shows all applied migrations in reverse chronological order.

### View Pending Migrations

```bash
alembic heads
```

Shows which branch is the latest.

## Common Workflow

### Day-to-Day Development

1. Update models in `src/models/domain.py`
2. Generate migration: `alembic revision --autogenerate -m "Add new field"`
3. Review generated migration file in `alembic/versions/`
4. Apply migration: `alembic upgrade head`
5. Test your changes
6. Commit migration file to git

### Before Deployment

1. Run all pending migrations locally: `alembic upgrade head`
2. Test the application with updated schema
3. Verify migration can be reverted: `alembic downgrade -1` then `alembic upgrade head`
4. Commit all migration files

## Troubleshooting

### "No such table: alembic_version"

The `alembic_version` table is created automatically on first migration. If it doesn't exist:

```bash
alembic stamp head
```

This marks the database as at the latest version without actually running migrations.

### Migration Conflicts

If multiple branches have different migration histories:

1. Check history: `alembic history --oneline`
2. Identify conflicting migrations
3. Manually merge or create a new migration to reconcile

### Connection Issues

If Alembic can't connect to the database:

1. Verify `DATABASE_URL` environment variable is set correctly
2. Check PostgreSQL is running: `psql -l`
3. Test connection: `psql $DATABASE_URL`
4. Check firewall and network settings

## Database Schema Restoration

To reset the database to an empty state:

```bash
# Drop and recreate the database
dropdb fundlens
createdb fundlens

# Mark database as at version 0
alembic stamp base
```

Then apply migrations normally: `alembic upgrade head`

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
