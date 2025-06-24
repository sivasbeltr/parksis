from datetime import date

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import AboneEndeks, Park, ParkAbone


class ParkAboneForm(forms.ModelForm):
    class Meta:
        model = ParkAbone
        fields = [
            "park",
            "abone_tipi",
            "abone_no",
            "abone_tarihi",
            "ilk_endeks",
            "geom",
        ]
        widgets = {
            "park": forms.Select(
                attrs={
                    "class": "block w-full px-3 py-2 bg-white dark:bg-gray-800 border-2 border-gray-300 dark:border-gray-600 rounded-lg shadow-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500",
                }
            ),
            "abone_tipi": forms.Select(
                attrs={
                    "class": "block w-full px-3 py-2 bg-white dark:bg-gray-800 border-2 border-gray-300 dark:border-gray-600 rounded-lg shadow-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500",
                }
            ),
            "abone_no": forms.TextInput(
                attrs={
                    "class": "block w-full px-3 py-2 bg-white dark:bg-gray-800 border-2 border-gray-300 dark:border-gray-600 rounded-lg shadow-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500",
                    "placeholder": "Abone numarasını giriniz",
                }
            ),
            "abone_tarihi": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "block w-full px-3 py-2 bg-white dark:bg-gray-800 border-2 border-gray-300 dark:border-gray-600 rounded-lg shadow-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500",
                }
            ),
            "ilk_endeks": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0",
                    "class": "block w-full px-3 py-2 bg-white dark:bg-gray-800 border-2 border-gray-300 dark:border-gray-600 rounded-lg shadow-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500",
                    "placeholder": "İlk endeks değerini giriniz",
                }
            ),
            "geom": forms.HiddenInput(),
        }
        labels = {
            "park": _("Park"),
            "abone_tipi": _("Abone Tipi"),
            "abone_no": _("Abone Numarası"),
            "abone_tarihi": _("Abone Tarihi"),
            "ilk_endeks": _("İlk Endeks Değeri"),
        }
        help_texts = {
            "park": _("Abonenin bağlı olduğu parkı seçiniz"),
            "abone_tipi": _("Abonelik tipini seçiniz"),
            "abone_no": _("Benzersiz abone numarasını giriniz"),
            "abone_tarihi": _("Abonelik başlangıç tarihini seçiniz"),
            "ilk_endeks": _("Aboneliğin başlangıç endeks değerini giriniz (zorunlu)"),
        }

    def __init__(self, *args, **kwargs):
        self.park_uuid = kwargs.pop("park_uuid", None)
        super().__init__(*args, **kwargs)

        # Eğer park_uuid verilmişse, sadece o parkı seç ve gizle
        if self.park_uuid:
            try:
                park = Park.objects.get(uuid=self.park_uuid)
                self.fields["park"].initial = park
                self.fields["park"].widget = forms.HiddenInput()
            except Park.DoesNotExist:
                pass

        # Park seçeneklerini optimize et
        self.fields["park"].queryset = Park.objects.select_related(
            "mahalle", "mahalle__ilce"
        ).order_by("mahalle__ilce__ad", "mahalle__ad", "ad")

        if not self.instance.pk:
            self.fields["abone_tarihi"].initial = date.today()
            self.fields["ilk_endeks"].initial = 0.0

        # İlk endeks alanını zorunlu yap
        self.fields["ilk_endeks"].required = True

    def clean_abone_no(self):
        abone_no = self.cleaned_data.get("abone_no")
        park = self.cleaned_data.get("park")
        abone_tipi = self.cleaned_data.get("abone_tipi")

        if not abone_no:
            raise ValidationError(_("Abone numarası zorunludur."))

        # Aynı park ve abone tipinde aynı numara olmasın
        existing = ParkAbone.objects.filter(
            park=park, abone_tipi=abone_tipi, abone_no=abone_no
        ).exclude(pk=self.instance.pk)

        if existing.exists():
            raise ValidationError(
                _("Bu park ve abone tipi için bu numara zaten kullanılıyor.")
            )

        return abone_no

    def clean_abone_tarihi(self):
        abone_tarihi = self.cleaned_data.get("abone_tarihi")
        if abone_tarihi and abone_tarihi > date.today():
            raise ValidationError(_("Abone tarihi bugünden ileri olamaz."))
        return abone_tarihi

    def clean_ilk_endeks(self):
        ilk_endeks = self.cleaned_data.get("ilk_endeks")
        if ilk_endeks is None:
            raise ValidationError(_("İlk endeks değeri zorunludur."))
        if ilk_endeks < 0:
            raise ValidationError(_("İlk endeks değeri negatif olamaz."))
        return ilk_endeks


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
            # Son endeks değeri ile karşılaştır (en büyük endeks değeri)
            son_endeks = (
                AboneEndeks.objects.filter(park_abone=self.park_abone)
                .exclude(pk=self.instance.pk)
                .order_by("-endeks_degeri")
                .first()
            )

            # Eğer hiç endeks yoksa, ilk endeks değeri ile karşılaştır
            if not son_endeks:
                ilk_endeks = self.park_abone.ilk_endeks or 0
                if endeks_degeri < ilk_endeks:
                    raise ValidationError(
                        _("Endeks değeri ilk endeks değerinden (%(val)s) küçük olamaz.")
                        % {"val": ilk_endeks}
                    )
            else:
                if endeks_degeri < son_endeks.endeks_degeri:
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


class MobilEndeksForm(forms.ModelForm):
    """Mobil uygulama için basitleştirilmiş endeks formu"""

    class Meta:
        model = AboneEndeks
        fields = ["endeks_tarihi", "endeks_degeri"]
        widgets = {
            "endeks_tarihi": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full px-4 py-3 text-lg bg-white border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500",
                }
            ),
            "endeks_degeri": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0",
                    "class": "w-full px-4 py-3 text-lg bg-white border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500",
                    "placeholder": "Endeks değerini giriniz",
                    "inputmode": "decimal",
                }
            ),
        }
        labels = {
            "endeks_tarihi": _("Okuma Tarihi"),
            "endeks_degeri": _("Endeks Değeri"),
        }

    def __init__(self, *args, **kwargs):
        self.park_abone = kwargs.pop("park_abone", None)
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields["endeks_tarihi"].initial = date.today()

    def clean_endeks_degeri(self):
        endeks_degeri = self.cleaned_data.get("endeks_degeri")
        if endeks_degeri is None:
            raise ValidationError(_("Endeks değeri zorunludur."))
        if endeks_degeri < 0:
            raise ValidationError(_("Endeks değeri negatif olamaz."))

        if self.park_abone:
            # Son endeks değeri ile karşılaştır (en büyük endeks değeri)
            son_endeks = (
                AboneEndeks.objects.filter(park_abone=self.park_abone)
                .exclude(pk=self.instance.pk)
                .order_by("-endeks_degeri")
                .first()
            )

            # Eğer hiç endeks yoksa, ilk endeks değeri ile karşılaştır
            if not son_endeks:
                ilk_endeks = self.park_abone.ilk_endeks or 0
                if endeks_degeri < ilk_endeks:
                    raise ValidationError(
                        _("Endeks değeri ilk endeks değerinden (%(val)s) küçük olamaz.")
                        % {"val": ilk_endeks}
                    )
            else:
                if endeks_degeri < son_endeks.endeks_degeri:
                    raise ValidationError(
                        _("Endeks değeri son kayıtlı değerden (%(val)s) küçük olamaz.")
                        % {"val": son_endeks.endeks_degeri}
                    )

        return endeks_degeri
