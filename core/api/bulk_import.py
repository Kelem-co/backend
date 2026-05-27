from django.http import HttpResponse
from django.template.loader import render_to_string


def build_bulk_import_template_response(
    *,
    template_name: str,
    filename: str,
) -> HttpResponse:
    response = HttpResponse(
        render_to_string(template_name),
        content_type="text/csv; charset=utf-8",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
