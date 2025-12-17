from common.models import Country
from django import forms

from .models import Creative, CreativeGeoData


class CreativeGeoDataForm(forms.ModelForm):
    country = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        required=True,
        label="Country",
        empty_label="Select a country",
    )
    hook = forms.IntegerField(
        label="Hook",
        help_text="Укажите значение hook",
    )
    hold = forms.IntegerField(
        label="Hold",
        help_text="Укажите значение hold",
    )
    ctr = forms.IntegerField(
        label="CTR",
        help_text="Укажите значение CTR",
    )
    comment = forms.CharField(
        required=False,
        label="Комментарий",
        help_text="Можно оставить пустым",
    )

    class Meta:
        model = CreativeGeoData
        fields = ["hook", "hold", "ctr", "comment", "country"]

    def __init__(self, *args, creative: Creative, **kwargs):  # noqa: ANN002, ANN003
        self.creative = creative
        super().__init__(*args, **kwargs)

    def clean(self) -> dict:
        cleaned_data = super().clean()
        country = cleaned_data.get("country")

        if (
            country
            and CreativeGeoData.objects.filter(
                creative=self.creative,
                country=country,
            )
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError(f"Для этого креатива данные по {country} уже существуют.")

        return cleaned_data
