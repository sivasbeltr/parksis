from django import forms
from django.contrib.auth.models import Group, User
from django.contrib.gis.forms import PointField
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from ortak.models import Mahalle
from parkbahce.models import Park

from .models import (
    Gorev,
    GorevAsama,
    GorevTamamlamaResim,
    GunlukKontrol,
    KontrolResim,
    ParkPersonel,
    Personel,
)


class MobilKontrolForm(forms.ModelForm):
    """
    Mobil saha personeli için günlük kontrol formu
    """

    # Resim alanları
    resim_1 = forms.ImageField(
        label=_("Resim 1"),
        required=False,
        widget=forms.FileInput(
            attrs={
                "class": "hidden",
                "accept": "image/jpeg,image/png",
            }
        ),
    )

    resim_2 = forms.ImageField(
        label=_("Resim 2"),
        required=False,
        widget=forms.FileInput(
            attrs={
                "class": "hidden",
                "accept": "image/jpeg,image/png",
            }
        ),
    )

    resim_3 = forms.ImageField(
        label=_("Resim 3"),
        required=False,
        widget=forms.FileInput(
            attrs={
                "class": "hidden",
                "accept": "image/jpeg,image/png",
            }
        ),
    )

    resim_aciklama_1 = forms.CharField(
        label=_("Resim 1 Açıklaması"),
        required=False,
        max_length=200,
        widget=forms.TextInput(
            attrs={
                "class": "flex-1 p-1.5 border border-gray-300 rounded-lg text-xs",
                "placeholder": "Açıklama (opsiyonel)",
            }
        ),
    )

    resim_aciklama_2 = forms.CharField(
        label=_("Resim 2 Açıklaması"),
        required=False,
        max_length=200,
        widget=forms.TextInput(
            attrs={
                "class": "flex-1 p-1.5 border border-gray-300 rounded-lg text-xs",
                "placeholder": "Açıklama (opsiyonel)",
            }
        ),
    )

    resim_aciklama_3 = forms.CharField(
        label=_("Resim 3 Açıklaması"),
        required=False,
        max_length=200,
        widget=forms.TextInput(
            attrs={
                "class": "flex-1 p-1.5 border border-gray-300 rounded-lg text-xs",
                "placeholder": "Açıklama (opsiyonel)",
            }
        ),
    )

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


class PersonelKullaniciForm(forms.Form):
    """
    Kullanıcı ve Personel birleşik oluşturma formu
    """

    # Kullanıcı bilgileri
    kullanici_adi = forms.CharField(
        label=_("Kullanıcı Adı"),
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 bg-white border-2 border-gray-300 rounded-xl text-base font-medium focus:ring-2 focus:ring-park-green-500 focus:border-park-green-500 transition-all",
                "placeholder": "Benzersiz kullanıcı adı giriniz",
            }
        ),
    )

    eposta = forms.EmailField(
        label=_("E-posta"),
        required=False,
        widget=forms.EmailInput(
            attrs={
                "class": "w-full px-4 py-3 bg-white border-2 border-gray-300 rounded-xl text-base font-medium focus:ring-2 focus:ring-park-green-500 focus:border-park-green-500 transition-all",
                "placeholder": "ornek@belediye.gov.tr",
            }
        ),
    )
    sifre = forms.CharField(
        label=_("Şifre"),
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full px-4 py-3 bg-white border-2 border-gray-300 rounded-xl text-base font-medium focus:ring-2 focus:ring-park-green-500 focus:border-park-green-500 transition-all",
                "placeholder": "Güçlü bir şifre belirleyin",
            }
        ),
    )

    sifre_tekrar = forms.CharField(
        label=_("Şifre Tekrar"),
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full px-4 py-3 bg-white border-2 border-gray-300 rounded-xl text-base font-medium focus:ring-2 focus:ring-park-green-500 focus:border-park-green-500 transition-all",
                "placeholder": "Şifreyi tekrar giriniz",
            }
        ),
    )

    first_name = forms.CharField(
        label=_("Ad"),
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 bg-white border-2 border-gray-300 rounded-xl text-base font-medium focus:ring-2 focus:ring-park-green-500 focus:border-park-green-500 transition-all",
                "placeholder": "Personelin adı",
            }
        ),
    )

    last_name = forms.CharField(
        label=_("Soyad"),
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 bg-white border-2 border-gray-300 rounded-xl text-base font-medium focus:ring-2 focus:ring-park-green-500 focus:border-park-green-500 transition-all",
                "placeholder": "Personelin soyadı",
            }
        ),
    )

    is_active = forms.BooleanField(
        label=_("Aktif"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(
            attrs={
                "class": "w-5 h-5 text-park-green-600 border-2 border-gray-300 rounded focus:ring-park-green-500"
            }
        ),
    )

    # Personel bilgileri
    telefon = forms.CharField(
        label=_("Telefon"),
        max_length=15,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 bg-white border-2 border-gray-300 rounded-xl text-base font-medium focus:ring-2 focus:ring-park-green-500 focus:border-park-green-500 transition-all",
                "placeholder": "+90 555 123 45 67",
            }
        ),
    )

    pozisyon = forms.CharField(
        label=_("Pozisyon"),
        max_length=50,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 bg-white border-2 border-gray-300 rounded-xl text-base font-medium focus:ring-2 focus:ring-park-green-500 focus:border-park-green-500 transition-all",
                "placeholder": "Park Görevlisi, Teknik Personel vb.",
            }
        ),
    )

    # Gruplar
    groups = forms.ModelMultipleChoiceField(
        label=_("Kullanıcı Grupları"),
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(
            attrs={
                "class": "space-y-2",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        sifre = cleaned_data.get("sifre")
        sifre_tekrar = cleaned_data.get("sifre_tekrar")

        if sifre and sifre_tekrar:
            if sifre != sifre_tekrar:
                raise ValidationError(_("Şifreler eşleşmiyor."))

        return cleaned_data

    def clean_eposta(self):
        eposta = self.cleaned_data.get("eposta")
        if eposta and User.objects.filter(email=eposta).exists():
            raise ValidationError(_("Bu e-posta adresi zaten kullanılıyor."))
        return eposta


class ParkPersonelAtamaForm(forms.Form):
    """
    Personele park atama formu - HTMX ile kullanılacak
    """

    parklar = forms.ModelMultipleChoiceField(
        queryset=Park.objects.none(),
        widget=forms.CheckboxSelectMultiple(
            attrs={
                "class": "park-checkbox space-y-2",
            }
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        personel = kwargs.pop("personel", None)
        super().__init__(*args, **kwargs)

        if personel:
            # Mevcut atanmış parkları işaretle
            atanmis_parklar = ParkPersonel.objects.filter(
                personel=personel
            ).values_list("park_id", flat=True)
            self.fields["parklar"].queryset = Park.objects.select_related(
                "mahalle", "mahalle__ilce", "park_tipi"
            ).order_by("mahalle__ad", "ad")
            self.fields["parklar"].initial = atanmis_parklar


class GorevAsamaForm(forms.ModelForm):
    """
    Görev aşaması oluşturma ve düzenleme formu
    """

    class Meta:
        model = GorevAsama
        fields = ["ad", "aciklama", "sorumlu"]
        widgets = {
            "ad": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 bg-white border-2 border-gray-300 rounded-xl text-base font-medium focus:ring-2 focus:ring-park-green-500 focus:border-park-green-500 transition-all",
                    "placeholder": "Aşama adını giriniz (örn. Hazırlık, Uygulama, Kontrol)",
                }
            ),
            "aciklama": forms.Textarea(
                attrs={
                    "class": "w-full px-4 py-3 bg-white border-2 border-gray-300 rounded-xl text-base resize-none focus:ring-2 focus:ring-park-green-500 focus:border-park-green-500 transition-all",
                    "rows": 3,
                    "placeholder": "Aşama hakkında detaylı açıklama giriniz...",
                }
            ),
            "sorumlu": forms.Select(
                attrs={
                    "class": "w-full px-4 py-3 bg-white border-2 border-gray-300 rounded-xl text-base font-medium focus:ring-2 focus:ring-park-green-500 focus:border-park-green-500 transition-all",
                }
            ),
        }
        labels = {
            "ad": _("Aşama Adı"),
            "aciklama": _("Açıklama"),
            "sorumlu": _("Sorumlu Personel"),
        }

    def __init__(self, *args, **kwargs):
        gorev = kwargs.pop("gorev", None)
        super().__init__(*args, **kwargs)

        # Sadece aktif personelleri göster
        self.fields["sorumlu"].queryset = Personel.objects.filter(aktif=True).order_by(
            "ad"
        )
        self.fields["sorumlu"].empty_label = "Sorumlu personel seçiniz"

        # Eğer görev varsa, görevdeki atanmış personelleri öncelikli göster
        if gorev:
            atanan_personeller = gorev.atamalar.values_list("personel_id", flat=True)
            if atanan_personeller:
                self.fields["sorumlu"].queryset = Personel.objects.filter(
                    aktif=True
                ).order_by("-id__in=" + ",".join(map(str, atanan_personeller)), "ad")


class GorevDurumForm(forms.ModelForm):
    """
    Görev durum değişikliği formu
    """

    not_text = forms.CharField(
        label=_("Not"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "w-full px-4 py-3 bg-white border-2 border-gray-300 rounded-xl text-base resize-none focus:ring-2 focus:ring-park-green-500 focus:border-park-green-500 transition-all",
                "rows": 3,
                "placeholder": "Durum değişikliği ile ilgili notlarınızı yazabilirsiniz...",
            }
        ),
    )

    class Meta:
        model = Gorev
        fields = ["durum"]
        widgets = {
            "durum": forms.Select(
                attrs={
                    "class": "w-full px-4 py-3 bg-white border-2 border-gray-300 rounded-xl text-base font-medium focus:ring-2 focus:ring-park-green-500 focus:border-park-green-500 transition-all",
                }
            ),
        }
        labels = {
            "durum": _("Yeni Durum"),
        }


class GorevAsamaDurumForm(forms.ModelForm):
    """
    Görev aşama durum değişikliği formu
    """

    class Meta:
        model = GorevAsama
        fields = ["durum"]
        widgets = {
            "durum": forms.Select(
                attrs={
                    "class": "px-3 py-2 bg-white border-2 border-gray-300 rounded-lg text-sm font-medium focus:ring-2 focus:ring-park-green-500 focus:border-park-green-500 transition-all",
                }
            ),
        }
        labels = {
            "durum": _("Durum"),
        }
