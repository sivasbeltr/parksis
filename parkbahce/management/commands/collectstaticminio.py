"""
MinIO için özel collectstatic komutu
Django'nun standart collectstatic'i yerine MinIO'ya static dosyaları yükler
"""

import os
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.management.commands.collectstatic import (
    Command as BaseCommand,
)
from django.core.management.base import CommandError
from minio import Minio
from minio.error import S3Error


class Command(BaseCommand):
    help = "Static dosyaları MinIO'ya yükler"

    def __init__(self):
        super().__init__()
        self.minio_client = None
        self.bucket_name = None
        self.static_location = None

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="MinIO'daki mevcut static dosyaları önce sil",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Dosyaları yüklemeden sadece listele",
        )

    def handle(self, *args, **options):
        if not getattr(settings, "USE_MINIO", False):
            raise CommandError("MinIO devre dışı. USE_MINIO=True olarak ayarlayın.")

        # MinIO client'ını hazırla
        self._setup_minio()

        # Bucket kontrolü
        self._ensure_bucket_exists()

        # Mevcut dosyaları temizle (eğer istenirse)
        if options["clear"]:
            self._clear_static_files()

        # Static dosyaları topla ve yükle
        self._collect_and_upload_static_files(options["dry_run"])

    def _setup_minio(self):
        """MinIO client'ını kurulum yap"""
        try:
            self.minio_client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_USE_HTTPS,
            )
            self.bucket_name = settings.MINIO_BUCKET_NAME
            self.static_location = settings.MINIO_STATIC_LOCATION

            self.stdout.write(f"✅ MinIO bağlantısı kuruldu: {settings.MINIO_ENDPOINT}")
            self.stdout.write(f"📦 Bucket: {self.bucket_name}")
            self.stdout.write(f"📁 Static location: {self.static_location}")

        except Exception as e:
            raise CommandError(f"MinIO bağlantısı kurulamadı: {e}")

    def _ensure_bucket_exists(self):
        """Bucket'ın var olduğundan emin ol"""
        try:
            if not self.minio_client.bucket_exists(self.bucket_name):
                self.minio_client.make_bucket(self.bucket_name)
                self.stdout.write(f"✅ Bucket '{self.bucket_name}' oluşturuldu")
            else:
                self.stdout.write(f"✅ Bucket '{self.bucket_name}' mevcut")
        except S3Error as e:
            raise CommandError(f"Bucket kontrolü/oluşturma hatası: {e}")

    def _clear_static_files(self):
        """Mevcut static dosyaları temizle"""
        try:
            self.stdout.write("🗑️ Mevcut static dosyalar temizleniyor...")

            # Static location prefix'i ile tüm dosyaları listele
            objects = self.minio_client.list_objects(
                self.bucket_name, prefix=f"{self.static_location}/"
            )

            deleted_count = 0
            for obj in objects:
                self.minio_client.remove_object(self.bucket_name, obj.object_name)
                deleted_count += 1

            self.stdout.write(f"✅ {deleted_count} static dosya silindi")

        except S3Error as e:
            self.stdout.write(f"⚠️ Dosya temizleme hatası: {e}")

    def _collect_and_upload_static_files(self, dry_run=False):
        """Static dosyaları topla ve MinIO'ya yükle"""
        self.stdout.write("📂 Static dosyalar toplanıyor...")

        # Django'nun staticfiles finder'ını kullan
        found_files = {}

        # Tüm static dosyaları bul
        for finder in finders.get_finders():
            for path, storage in finder.list([]):
                # Dosya yolunu normalize et
                if path not in found_files:
                    found_files[path] = finder.find(path)

        total_files = len(found_files)
        uploaded_files = 0
        failed_files = 0

        self.stdout.write(f"📊 Toplam {total_files} static dosya bulundu")

        if dry_run:
            self.stdout.write("🔍 DRY RUN - Dosyalar:")
            for file_path in found_files.keys():
                # Windows path separator'ını düzelt
                normalized_path = file_path.replace("\\", "/")
                self.stdout.write(f"  - {normalized_path}")
            return

        self.stdout.write("⬆️ MinIO'ya yükleniyor...")

        for relative_path, absolute_path in found_files.items():
            try:
                # KRITIK: Windows path separator'ını Unix/Linux'a dönüştür
                relative_path = relative_path.replace("\\", "/")

                # MinIO'daki tam yol
                minio_path = f"{self.static_location}/{relative_path}"

                # Dosyayı oku
                with open(absolute_path, "rb") as file:
                    file_data = file.read()
                    file_size = len(file_data)

                    # Content type'ı belirle
                    content_type = self._get_content_type(relative_path)

                    # MinIO'ya yükle
                    from io import BytesIO

                    self.minio_client.put_object(
                        self.bucket_name,
                        minio_path,
                        BytesIO(file_data),
                        file_size,
                        content_type=content_type,
                    )

                    uploaded_files += 1

                    # Progress göster
                    if uploaded_files % 10 == 0:
                        self.stdout.write(
                            f"⬆️ {uploaded_files}/{total_files} dosya yüklendi..."
                        )

                    # Her dosya için debug bilgisi
                    if uploaded_files <= 5:  # İlk 5 dosya için detay göster
                        self.stdout.write(f"  ✅ {relative_path} -> {minio_path}")

            except Exception as e:
                failed_files += 1
                self.stdout.write(f"❌ Hata: {relative_path} - {e}")

        # Özet
        self.stdout.write(self.style.SUCCESS(f"✅ Tamamlandı!"))
        self.stdout.write(f"📊 Yüklenen: {uploaded_files}")
        self.stdout.write(f"❌ Başarısız: {failed_files}")

        if uploaded_files > 0:
            protocol = "https" if settings.MINIO_USE_HTTPS else "http"
            static_url = (
                f"{protocol}://{settings.MINIO_CUSTOM_DOMAIN}/{self.static_location}/"
            )
            self.stdout.write(f"🌐 Static URL: {static_url}")

    def _get_content_type(self, file_path):
        """Dosya uzantısına göre content type belirle"""
        import mimetypes

        content_type, _ = mimetypes.guess_type(file_path)

        # Varsayılan content type'lar
        if not content_type:
            ext = Path(file_path).suffix.lower()
            content_types = {
                ".css": "text/css",
                ".js": "application/javascript",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".svg": "image/svg+xml",
                ".ico": "image/x-icon",
                ".woff": "font/woff",
                ".woff2": "font/woff2",
                ".ttf": "font/ttf",
                ".eot": "application/vnd.ms-fontobject",
            }
            content_type = content_types.get(ext, "application/octet-stream")

        return content_type
