from datetime import date

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import AboneEndeks, ParkAbone


class EndeksForm(forms.ModelForm):
    class Meta:
        model = AboneEndeks
        fields = ["endeks_tarihi", "endeks_degeri"]
        widgets = {
            "endeks_tarihi": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "block w-full px-3 py-2 bg-white dark:bg-gray-800 border-2 border-gray-300 dark:border-gray-600 rounded-lg shadow-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-sm",
                }
            ),
            "endeks_degeri": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0",
                    "class": "block w-full px-3 py-2 bg-white dark:bg-gray-800 border-2 border-gray-300 dark:border-gray-600 rounded-lg shadow-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-sm",
                    "placeholder": "Endeks değerini giriniz",
                }
            ),
        }
        labels = {
            "endeks_tarihi": _("Endeks Tarihi"),
            "endeks_degeri": _("Endeks Değeri"),
        }
        help_texts = {
            "endeks_tarihi": _("Endeks okuma tarihini seçiniz"),
            "endeks_degeri": _("Okunan endeks değerini giriniz"),
        }

    def __init__(self, *args, **kwargs):
        self.park_abone = kwargs.pop("park_abone", None)
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields["endeks_tarihi"].initial = date.today()

    def clean_endeks_tarihi(self):
        endeks_tarihi = self.cleaned_data.get("endeks_tarihi")
        if not endeks_tarihi:
            raise ValidationError(_("Endeks tarihi zorunludur."))
        if endeks_tarihi > date.today():
            raise ValidationError(_("Endeks tarihi bugünden ileri olamaz."))
        if self.park_abone:
            existing = AboneEndeks.objects.filter(
                park_abone=self.park_abone, endeks_tarihi=endeks_tarihi
            ).exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError(_("Bu tarihte zaten bir endeks kaydı var."))
        return endeks_tarihi

    def clean_endeks_degeri(self):
        endeks_degeri = self.cleaned_data.get("endeks_degeri")
        if endeks_degeri is None:
            raise ValidationError(_("Endeks değeri zorunludur."))
        if endeks_degeri < 0:
            raise ValidationError(_("Endeks değeri negatif olamaz."))
        if self.park_abone:
            son_endeks = (
                AboneEndeks.objects.filter(park_abone=self.park_abone)
                .exclude(pk=self.instance.pk)
                .order_by("-endeks_tarihi")
                .first()
            )
            if son_endeks and endeks_degeri < son_endeks.endeks_degeri:
                raise ValidationError(
                    _("Endeks değeri son kayıtlı değerden (%(val)s) küçük olamaz.")
                    % {"val": son_endeks.endeks_degeri}
                )
        return endeks_degeri

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.park_abone:
            instance.park_abone = self.park_abone
        if commit:
            instance.save()
        return instance
