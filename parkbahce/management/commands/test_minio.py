"""
MinIO Test Management Command
MinIO bağlantısını ve bucket durumunu test etmek için
"""

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "MinIO bağlantısını ve bucket durumunu test eder"

    def add_arguments(self, parser):
        parser.add_argument(
            "--create-bucket",
            action="store_true",
            help="Bucket yoksa oluştur",
        )
        parser.add_argument(
            "--upload-test",
            action="store_true",
            help="Test dosyası yükle",
        )

    def handle(self, *args, **options):
        if not getattr(settings, "USE_MINIO", False):
            self.stdout.write(
                self.style.ERROR("MinIO devre dışı. USE_MINIO=True olarak ayarlayın.")
            )
            return

        if not hasattr(settings, "MINIO_ACCESS_KEY"):
            self.stdout.write(
                self.style.ERROR(
                    "MinIO ayarları bulunamadı. .env dosyasını kontrol edin."
                )
            )
            return

        try:
            # MinIO client oluştur (Python MinIO API kullanarak)
            from minio import Minio
            from minio.error import S3Error

            minio_client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_USE_HTTPS,
            )

            bucket_name = settings.MINIO_BUCKET_NAME

            self.stdout.write(f"MinIO Endpoint: {settings.MINIO_ENDPOINT}")
            self.stdout.write(f"Bucket Name: {bucket_name}")
            self.stdout.write(f"Custom Domain: {settings.MINIO_CUSTOM_DOMAIN}")

            # Bağlantı testi
            self.stdout.write("MinIO bağlantısı test ediliyor...")

            try:
                # Bucket listesini al
                buckets = minio_client.list_buckets()
                bucket_names = [bucket.name for bucket in buckets]
                self.stdout.write(self.style.SUCCESS("✓ MinIO bağlantısı başarılı!"))
                self.stdout.write(f"Mevcut bucket'lar: {bucket_names}")

                # Hedef bucket kontrolü
                if bucket_name in bucket_names:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Bucket "{bucket_name}" mevcut!')
                    )

                    # Bucket içeriğini listele
                    try:
                        objects = list(minio_client.list_objects(bucket_name))
                        if objects:
                            self.stdout.write(f"Bucket'ta {len(objects)} dosya bulundu")
                            for obj in objects[:5]:  # İlk 5'ini göster
                                self.stdout.write(
                                    f"  - {obj.object_name} ({obj.size} bytes)"
                                )
                        else:
                            self.stdout.write("Bucket boş")
                    except S3Error as e:
                        self.stdout.write(
                            self.style.WARNING(f"Bucket içeriği listelenemedi: {e}")
                        )

                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠ Bucket "{bucket_name}" bulunamadı!')
                    )

                    if options["create_bucket"]:
                        try:
                            minio_client.make_bucket(bucket_name)
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'✓ Bucket "{bucket_name}" oluşturuldu!'
                                )
                            )

                            # Bucket policy ayarla (public read)
                            bucket_policy = {
                                "Version": "2012-10-17",
                                "Statement": [
                                    {
                                        "Effect": "Allow",
                                        "Principal": "*",
                                        "Action": ["s3:GetObject"],
                                        "Resource": [f"arn:aws:s3:::{bucket_name}/*"],
                                    }
                                ],
                            }

                            import json

                            minio_client.set_bucket_policy(
                                bucket_name, json.dumps(bucket_policy)
                            )
                            self.stdout.write("✓ Bucket policy ayarlandı (public read)")

                        except S3Error as e:
                            self.stdout.write(
                                self.style.ERROR(f"✗ Bucket oluşturulamadı: {e}")
                            )

                # Test dosyası yükleme
                if options["upload_test"]:
                    test_content = "MinIO test dosyası - Django Akıllı Şehir Projesi"

                    # Static test
                    static_key = f"{settings.MINIO_STATIC_LOCATION}/test_static.txt"
                    try:
                        from io import BytesIO

                        test_data = BytesIO(test_content.encode("utf-8"))

                        minio_client.put_object(
                            bucket_name,
                            static_key,
                            test_data,
                            len(test_content.encode("utf-8")),
                            content_type="text/plain",
                        )

                        static_url = f"http://{settings.MINIO_CUSTOM_DOMAIN}/static/test_static.txt"
                        self.stdout.write(
                            self.style.SUCCESS(f"✓ Static test dosyası yüklendi!")
                        )
                        self.stdout.write(f"Static URL: {static_url}")

                        # Test dosyasını sil
                        minio_client.remove_object(bucket_name, static_key)
                        self.stdout.write("Static test dosyası silindi")

                    except S3Error as e:
                        self.stdout.write(
                            self.style.ERROR(f"✗ Static test dosyası yüklenemedi: {e}")
                        )

                    # Media test
                    media_key = f"{settings.MINIO_MEDIA_LOCATION}/test_media.txt"
                    try:
                        test_data = BytesIO(test_content.encode("utf-8"))

                        minio_client.put_object(
                            bucket_name,
                            media_key,
                            test_data,
                            len(test_content.encode("utf-8")),
                            content_type="text/plain",
                        )

                        media_url = f"http://{settings.MINIO_CUSTOM_DOMAIN}/media/test_media.txt"
                        self.stdout.write(
                            self.style.SUCCESS(f"✓ Media test dosyası yüklendi!")
                        )
                        self.stdout.write(f"Media URL: {media_url}")

                        # Test dosyasını sil
                        minio_client.remove_object(bucket_name, media_key)
                        self.stdout.write("Media test dosyası silindi")

                    except S3Error as e:
                        self.stdout.write(
                            self.style.ERROR(f"✗ Media test dosyası yüklenemedi: {e}")
                        )

            except S3Error as e:
                self.stdout.write(self.style.ERROR(f"✗ MinIO bağlantı hatası: {e}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Beklenmeyen hata: {e}"))

        # Storage backend test
        try:
            from django.core.files.storage import default_storage

            self.stdout.write("\nDjango Storage Backend Test:")
            self.stdout.write(f"Storage Class: {default_storage.__class__.__name__}")

            if hasattr(default_storage, "bucket_name"):
                self.stdout.write(f"Bucket: {default_storage.bucket_name}")

        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"Storage backend test edilemedi: {e}")
            )
