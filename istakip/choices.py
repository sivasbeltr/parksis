from django.utils.translation import gettext_lazy as _


# Görev Durumları
class GorevDurumChoices:
    PLANLANMIS = "planlanmis"
    DEVAM_EDIYOR = "devam_ediyor"
    ONAYA_GONDERILDI = "onaya_gonderildi"
    TAMAMLANDI = "tamamlandi"
    IPTAL = "iptal"
    GECIKMIS = "gecikmis"
    CHOICES = [
        (PLANLANMIS, _("Planlanmış")),
        (DEVAM_EDIYOR, _("Devam Ediyor")),
        (ONAYA_GONDERILDI, _("Onaya Gönderildi")),
        (TAMAMLANDI, _("Tamamlandı")),
        (IPTAL, _("İptal")),
        (GECIKMIS, _("Gecikmiş")),
    ]


GOREV_DURUM_COLORS = {
    "planlanmis": {
        "color": "#F59E0B",
        "bg": "bg-yellow-100",
        "text": "text-yellow-600",
    },
    "devam_ediyor": {
        "color": "#F59E0B",
        "bg": "bg-amber-100",
        "text": "text-amber-600",
    },
    "onaya_gonderildi": {
        "color": "#8B5CF6",
        "bg": "bg-purple-100",
        "text": "text-purple-600",
    },
    "tamamlandi": {"color": "#10B981", "bg": "bg-green-100", "text": "text-green-600"},
    "iptal": {"color": "#EF4444", "bg": "bg-red-100", "text": "text-red-600"},
    "gecikmis": {"color": "#F97316", "bg": "bg-orange-100", "text": "text-orange-600"},
}


# Görev Öncelik
class GorevOncelikChoices:
    DUSUK = "dusuk"
    NORMAL = "normal"
    YUKSEK = "yuksek"
    ACIL = "acil"
    CHOICES = [
        (DUSUK, _("Düşük")),
        (NORMAL, _("Normal")),
        (YUKSEK, _("Yüksek")),
        (ACIL, _("Acil")),
    ]


GOREV_ONCELIK_COLORS = {
    "dusuk": {"color": "#6B7280", "bg": "bg-gray-100", "text": "text-gray-600"},
    "normal": {"color": "#3B82F6", "bg": "bg-blue-100", "text": "text-blue-600"},
    "yuksek": {"color": "#F59E0B", "bg": "bg-orange-100", "text": "text-orange-600"},
    "acil": {"color": "#EF4444", "bg": "bg-red-100", "text": "text-red-600"},
}


# Görev Tekrarlama
class GorevTekrarlamaChoices:
    YOK = "yok"
    GUNLUK = "gunluk"
    HAFTALIK = "haftalik"
    AYLIK = "aylik"
    YILLIK = "yillik"
    CHOICES = [
        (YOK, _("Tekrar Yok")),
        (GUNLUK, _("Günlük")),
        (HAFTALIK, _("Haftalık")),
        (AYLIK, _("Aylık")),
        (YILLIK, _("Yıllık")),
    ]


# Kontrol Durumları
class KontrolDurumChoices:
    SORUN_YOK = "sorun_yok"
    SORUN_VAR = "sorun_var"
    ACIL = "acil"
    GOZDEN_GECIRILDI = "gozden_gecirildi"
    ISE_DONUSTURULDU = "ise_donusturuldu"
    COZULDU = "cozuldu"
    CHOICES = [
        (SORUN_YOK, _("Sorun Yok")),
        (SORUN_VAR, _("Sorun Var")),
        (ACIL, _("Acil Müdahale Gerekli")),
        (GOZDEN_GECIRILDI, _("Gözden Geçirildi")),
        (ISE_DONUSTURULDU, _("İşe Dönüştürüldü")),
        (COZULDU, _("Çözüldü")),
    ]


KONTROL_DURUM_COLORS = {
    "sorun_yok": {"color": "#59AAF7", "bg": "bg-green-100", "text": "text-green-600"},
    "sorun_var": {"color": "#EF4444", "bg": "bg-red-100", "text": "text-red-600"},
    "acil": {"color": "#DC2626", "bg": "bg-red-200", "text": "text-red-700"},
    "gozden_gecirildi": {
        "color": "#F59E0B",
        "bg": "bg-orange-100",
        "text": "text-orange-600",
    },
    "ise_donusturuldu": {
        "color": "#8B5CF6",
        "bg": "bg-purple-100",
        "text": "text-purple-600",
    },
    "cozuldu": {"color": "#10B981", "bg": "bg-green-100", "text": "text-green-600"},
}


# Kontrol Tipi
class KontrolTipiChoices:
    RUTIN = "rutin"
    OZEL = "ozel"
    DENETIM = "denetim"
    CHOICES = [
        (RUTIN, _("Rutin Kontrol")),
        (OZEL, _("Özel Kontrol")),
        (DENETIM, _("Denetim")),
    ]


# Görev Aşama Durumları
class GorevAsamaDurumChoices:
    BEKLEMEDE = "beklemede"
    BASLAMADI = "baslamadi"
    DEVAM_EDIYOR = "devam_ediyor"
    TAMAMLANDI = "tamamlandi"
    CHOICES = [
        (BEKLEMEDE, _("Beklemede")),
        (BASLAMADI, _("Başlamadı")),
        (DEVAM_EDIYOR, _("Devam Ediyor")),
        (TAMAMLANDI, _("Tamamlandı")),
    ]


GOREV_ASAMA_DURUM_COLORS = {
    "beklemede": {"color": "#F59E0B", "bg": "bg-yellow-100", "text": "text-yellow-600"},
    "baslamadi": {"color": "#6B7280", "bg": "bg-gray-100", "text": "text-gray-600"},
    "devam_ediyor": {"color": "#3B82F6", "bg": "bg-blue-100", "text": "text-blue-600"},
    "tamamlandi": {"color": "#10B981", "bg": "bg-green-100", "text": "text-green-600"},
}


# Yardımcı fonksiyonlar
def get_gorev_durum_color(durum):
    return GOREV_DURUM_COLORS.get(durum, GOREV_DURUM_COLORS["planlanmis"])


def get_gorev_oncelik_color(oncelik):
    return GOREV_ONCELIK_COLORS.get(oncelik, GOREV_ONCELIK_COLORS["normal"])


def get_kontrol_durum_color(durum):
    return KONTROL_DURUM_COLORS.get(durum, KONTROL_DURUM_COLORS["sorun_yok"])


def get_gorev_asama_durum_color(durum):
    return GOREV_ASAMA_DURUM_COLORS.get(durum, GOREV_ASAMA_DURUM_COLORS["beklemede"])


def global_choices_context(request):
    from istakip import choices

    return {
        "GOREV_DURUM_CHOICES": choices.GorevDurumChoices.CHOICES,
        "GOREV_DURUM_COLORS": choices.GOREV_DURUM_COLORS,
        "GOREV_ONCELIK_CHOICES": choices.GorevOncelikChoices.CHOICES,
        "GOREV_ONCELIK_COLORS": choices.GOREV_ONCELIK_COLORS,
        "KONTROL_DURUM_CHOICES": choices.KontrolDurumChoices.CHOICES,
        "KONTROL_DURUM_COLORS": choices.KONTROL_DURUM_COLORS,
        "KONTROL_TIPI_CHOICES": choices.KontrolTipiChoices.CHOICES,
        "GOREV_ASAMA_DURUM_CHOICES": choices.GorevAsamaDurumChoices.CHOICES,
        "GOREV_ASAMA_DURUM_COLORS": choices.GOREV_ASAMA_DURUM_COLORS,
        "get_gorev_durum_color": choices.get_gorev_durum_color,
        "get_gorev_oncelik_color": choices.get_gorev_oncelik_color,
        "get_kontrol_durum_color": choices.get_kontrol_durum_color,
        "get_gorev_asama_durum_color": choices.get_gorev_asama_durum_color,
    }
