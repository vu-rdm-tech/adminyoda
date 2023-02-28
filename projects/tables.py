import django_tables2 as tables
from django.utils.html import format_html
import datetime


class ProjectTable(tables.Table):
    id = tables.Column()
    title = tables.Column()
    department = tables.Column()
    faculty = tables.Column()
    # requested_size = tables.Column()
    # limit = tables.Column()
    num_groups = tables.Column()
    num_dataset = tables.Column()
    num_published = tables.Column()
    # size_warning = tables.Column()
    size = tables.Column()
    created = tables.Column()

    def render_id(self, value):
        return format_html(f'<a href="{value}">{value}</>')

    def render_created(self, value):
        return value.strftime("%Y-%m-%d")

    class Meta:
        attrs = {"class": "table"}
        template_name = "django_tables2/bootstrap4.html"
