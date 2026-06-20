from django.apps import AppConfig


class SupportConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "hello_world.support"

    def ready(self):
        import hello_world.support.signals  # noqa: F401
