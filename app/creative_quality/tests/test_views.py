from http import HTTPStatus
from unittest.mock import patch

import pytest
from common.models import Country
from django.test import Client
from django.urls import reverse

from creative_quality.models import Creative, CreativeGeoData, CreativeGeoDataStatus, Task


@pytest.fixture()
def creative_task() -> tuple[Creative, Task]:
    task = Task.objects.create(task_id="xxx")
    creative = Creative.objects.create(task=task)
    return creative, task


@pytest.fixture()
def country_by() -> Country:
    return Country.objects.create(name="Belarus", iso_code="by")


@pytest.fixture()
def country_ru() -> Country:
    return Country.objects.create(name="Russia", iso_code="ru")


@pytest.mark.django_db()
class TestCreativeView:
    def test_get(self, creative_task: tuple[Creative, Task], client: Client):
        creative, task = creative_task
        url = reverse(
            "creative_quality:creative_detail",
            kwargs={
                "creative_pk": creative.pk,
                "task_id": task.task_id,
            },
        )
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_not_found(self, client: Client):
        url = reverse(
            "creative_quality:creative_detail",
            kwargs={
                "creative_pk": 1,
                "task_id": 1,
            },
        )
        response = client.get(url)
        assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db()
class TestCreativeEstimateView:
    def test_post(self, creative_task: tuple[Creative, Task], client: Client):
        creative, task = creative_task
        url = reverse(
            "creative_quality:creative_mark_estimate",
            kwargs={
                "creative_pk": creative.pk,
            },
        )
        with patch("creative_quality.views.CreativeService.end_estimate") as mock:
            response = client.post(url)
            assert response.status_code == HTTPStatus.FOUND
            mock.assert_called_once()

    def test_not_found(self, client: Client):
        url = reverse(
            "creative_quality:creative_mark_estimate",
            kwargs={
                "creative_pk": 1,
            },
        )
        response = client.post(url)
        assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db()
class TestCreativeGeoDataDetailView:
    def test_post(
        self,
        creative_task: tuple[Creative, Task],
        client: Client,
        country_by: Country,
        country_ru: Country,
    ):
        creative, task = creative_task
        geo_data = CreativeGeoData.objects.create(creative=creative, hold=0, hook=0, ctr=0, country=country_by)
        data = {
            "hold": 1,
            "hook": 2,
            "ctr": 3,
            "country": country_ru.pk,
            "status": CreativeGeoDataStatus.ZASHEL.value,
        }
        url = reverse("creative_quality:creative_geo_data", kwargs={"geo_data_pk": geo_data.pk})
        response = client.post(url, data=data)
        assert response.status_code == HTTPStatus.FOUND
        geo_data.refresh_from_db()
        assert geo_data.hold == 1
        assert geo_data.hook == 2  # noqa: PLR2004
        assert geo_data.ctr == 3  # noqa: PLR2004
        assert geo_data.country == country_ru
        assert geo_data.status == CreativeGeoDataStatus.ZASHEL.value


@pytest.mark.django_db()
class TestCreativeGeoDataCreateView:
    def test_post(self, creative_task: tuple[Creative, Task], client: Client, country_ru: Country):
        creative, task = creative_task
        data = {
            "hold": 1,
            "hook": 2,
            "ctr": 3,
            "country": country_ru.pk,
            "status": CreativeGeoDataStatus.NE_ZASHEL.value,
        }
        url = reverse("creative_quality:creative_geo_data_create", kwargs={"creative_pk": creative.pk})
        response = client.post(url, data=data)
        assert response.status_code == HTTPStatus.FOUND
        assert creative.geo_data.count() == 1
        geo_data = CreativeGeoData.objects.get(creative=creative)
        assert geo_data.hold == 1
        assert geo_data.hook == 2  # noqa: PLR2004
        assert geo_data.ctr == 3  # noqa: PLR2004
        assert geo_data.country == country_ru
        assert geo_data.status == CreativeGeoDataStatus.NE_ZASHEL.value


@pytest.mark.django_db()
class TestCreativeGeoDataDeleteView:
    def test_delete(self, creative_task: tuple[Creative, Task], client: Client, country_by: Country):
        creative, task = creative_task
        geo_data = CreativeGeoData.objects.create(creative=creative, hold=0, hook=0, ctr=0, country=country_by)
        url = reverse("creative_quality:creative_geo_data_delete", kwargs={"geo_data_pk": geo_data.pk})
        response = client.post(url)
        assert response.status_code == HTTPStatus.FOUND
        with pytest.raises(CreativeGeoData.DoesNotExist):
            CreativeGeoData.objects.get(pk=geo_data.pk)
