from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ("analytics", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS analytics_notification (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED,
                    type VARCHAR(10) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    message TEXT NOT NULL,
                    is_read BOOL NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL
                );
                CREATE INDEX IF NOT EXISTS analytics_notification_user_id_idx
                ON analytics_notification(user_id);
                CREATE INDEX IF NOT EXISTS analytics_notification_is_read_idx
                ON analytics_notification(is_read);
            """,
            reverse_sql="""
                DROP TABLE IF EXISTS analytics_notification;
            """,
        )
    ]
