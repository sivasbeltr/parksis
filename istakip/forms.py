from django import forms
from django.contrib.gis.forms import PointField
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from parkbahce.models import Park

from .models import Gorev, GorevAsama, GorevTamamlamaResim, GunlukKontrol, KontrolResim


class MobilKontrolForm(forms.ModelForm):
    """
    Mobil saha personeli için günlük kontrol formu
    """

    class Meta:
        model = GunlukKontrol
        fields = ["durum", "aciklama", "geom"]
        widgets = {
            "durum": forms.Select(
                attrs={
                    "class": "w-full p-4 bg-white border-2 border-gray-300 rounded-xl text-lg font-medium focus:ring-2 focus:ring-park-green-500 focus:border-park-green-500",
                }
            ),
            "aciklama": forms.Textarea(
                attrs={
                    "class": "w-full p-4 bg-white border-2 border-gray-300 rounded-xl text-lg resize-none focus:ring-2 focus:ring-park-green-500 focus:border-park-green-500",
                    "rows": 4,
                    "placeholder": "Sorun hakkında detayları açıklayın...",
                }
            ),
            "geom": forms.HiddenInput(),
        }
        labels = {
            "durum": _("Durum"),
            "aciklama": _("Açıklama"),
        }

    def __init__(self, *args, **kwargs):
        self.park = kwargs.pop("park", None)
        self.personel = kwargs.pop("personel", None)
        super().__init__(*args, **kwargs)

        # Sadece sorun durumlarını göster
        self.fields["durum"].choices = [
            ("sorun_yok", _("Sorun Yok")),
            ("sorun_var", _("Sorun Var")),
            ("acil", _("Acil Müdahale Gerekli")),
        ]

    def clean_aciklama(self):
        durum = self.cleaned_data.get("durum")
        aciklama = self.cleaned_data.get("aciklama")

        if durum in ["sorun_var", "acil"] and not aciklama:
            raise ValidationError(_("Sorun varsa açıklama zorunludur."))

        return aciklama

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.park:
            instance.park = self.park
        if self.personel:
            instance.personel = self.personel
        if commit:
            instance.save()
        return instance


class MobilKontrolResimForm(forms.ModelForm):
    """
    Mobil kontrol resim formu
    """

    class Meta:
        model = KontrolResim
        fields = ["resim", "aciklama"]
        widgets = {
            "resim": forms.FileInput(
                attrs={
                    "class": "w-full p-4 bg-white border-2 border-gray-300 rounded-xl text-lg file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-park-green-50 file:text-park-green-700 hover:file:bg-park-green-100",
                    "accept": "image/*",
                    "capture": "environment",  # Arka kamera
                }
            ),
            "aciklama": forms.TextInput(
                attrs={
                    "class": "w-full p-4 bg-white border-2 border-gray-300 rounded-xl text-lg focus:ring-2 focus:ring-park-green-500 focus:border-park-green-500",
                    "placeholder": "Resim açıklaması (opsiyonel)",
                }
            ),
        }
        labels = {
            "resim": _("Resim"),
            "aciklama": _("Resim Açıklaması"),
        }
