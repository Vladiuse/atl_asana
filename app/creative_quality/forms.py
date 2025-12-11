from django import forms

from .models import Creative


class CreativeForm(forms.ModelForm):
    hook = forms.IntegerField(
        label="Hook",
        help_text="Укажите значение hook",
    )
    hold = forms.IntegerField(
        label="Hold",
        help_text="Укажите значение hold",
    )
    crt = forms.IntegerField(
        label="CRT",
        help_text="Укажите значение CTR",
    )

    class Meta:
        model = Creative
        fields = ["hook", "hold", "crt"]