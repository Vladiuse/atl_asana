from typing import Any

from common.models import Country
from django import forms

from .models import CreativeAdaptation, CreativeGeoData, CreativeGeoDataStatus


class CreativeGeoDataForm(forms.ModelForm):  # type: ignore[type-arg]
    country = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        required=True,
        label="Country",
        empty_label="Select a country",
    )
    status = forms.ChoiceField(
        choices=[("", "— выберите статус —"), *CreativeGeoDataStatus.choices],
        label="Status",
        initial="",
        help_text="Укажите статус",
    )
    hook = forms.DecimalField(
        label="Hook",
        help_text="Укажите значение hook в %",
        decimal_places=2,
    )
    hold = forms.DecimalField(
        label="Hold",
        help_text="Укажите значение hold в %",
        decimal_places=2,
    )
    ctr = forms.DecimalField(
        label="CTR",
        help_text="Укажите значение CTR в %",
        decimal_places=2,
    )
    comment = forms.CharField(
        required=False,
        label="Комментарий",
        help_text="Можно оставить пустым",
    )

    class Meta:
        model = CreativeGeoData
        fields = ("hook", "hold", "ctr", "comment", "country", "status")

    def __init__(self, *args: Any, creative_adaptation: CreativeAdaptation, **kwargs: Any):  # noqa: ANN401
        self.creative_adaptation = creative_adaptation
        super().__init__(*args, **kwargs)

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        if cleaned_data is None:
            cleaned_data = {}
        country = cleaned_data.get("country")
        if (
            country
            and CreativeGeoData.objects.filter(
                creative_adaptation=self.creative_adaptation,
                country=country,
            )
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            msg = f"Для этого креатива данные по {country} уже существуют."
            raise forms.ValidationError(msg)

        return cleaned_data
