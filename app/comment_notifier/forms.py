from asana.client import AsanaApiClient
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from .models import ProjectIgnoredSection

asana_api_client = AsanaApiClient(api_key=settings.ASANA_API_KEY)


class ProjectIgnoredSectionForm(forms.ModelForm):
    class Meta:
        model = ProjectIgnoredSection
        fields = "__all__"

    def clean(self) -> None:
        """
        Raises:
            AsanaApiClientError
        """
        data = super().clean()
        if data["project"] and data.get("section_id"):
            project_sections = asana_api_client.get_project_sections(project_id=data["project"].project_id)
            project_section_ids = [section["gid"] for section in project_sections]
            if data["section_id"] not in project_section_ids:
                raise ValidationError(f"Section {data['section_id']} not found in project {project_sections} sections")
