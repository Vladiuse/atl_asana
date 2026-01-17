from unittest.mock import Mock

import pytest
from asana.client import AsanaApiClient

from creative_quality.models import CreativeProjectSection
from creative_quality.services import CreativeProjectSectionService


@pytest.mark.django_db
class TestCreativeProjectSectionService:
    def test_correct_save(self) -> None:
        mock_sana = Mock(spec=AsanaApiClient)
        mock_sana.get_section.return_value = {
            "name": "111",
            "project": {"name": "222"},
        }
        service = CreativeProjectSectionService(asana_api_client=mock_sana)
        section = CreativeProjectSection.objects.create(section_id=100)
        service.update_additional_info(creative_project_section=section)
        section.refresh_from_db()
        assert section.section_name == "111"
        assert section.project_name == "222"
        mock_sana.get_section.assert_called_once_with(section_id=100)
