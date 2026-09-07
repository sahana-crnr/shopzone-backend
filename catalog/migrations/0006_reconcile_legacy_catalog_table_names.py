from django.db import migrations


def rename_if_legacy_table_exists(old_name, new_name):
    return f"""
    DO $$
    BEGIN
        IF to_regclass('public.{old_name}') IS NOT NULL
           AND to_regclass('public.{new_name}') IS NULL THEN
            ALTER TABLE {old_name} RENAME TO {new_name};
        END IF;
    END $$;
    """


class Migration(migrations.Migration):
    """Reconcile databases created before custom db_table metadata was added."""
    dependencies = [("catalog", "0005_productreview")]

    operations = [
        migrations.RunSQL(rename_if_legacy_table_exists("catalog_product", "products"), migrations.RunSQL.noop),
        migrations.RunSQL(rename_if_legacy_table_exists("catalog_producttag", "product_tags"), migrations.RunSQL.noop),
        migrations.RunSQL(rename_if_legacy_table_exists("catalog_product_tags", "products_tags"), migrations.RunSQL.noop),
        migrations.RunSQL(rename_if_legacy_table_exists("catalog_productreview", "product_reviews"), migrations.RunSQL.noop),
    ]
