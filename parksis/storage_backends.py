"""
MinIO Storage Backends
Django için MinIO Python API kullanarak custom storage backend'leri
"""

from io import BytesIO
from urllib.parse import urljoin

from django.conf import settings
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from minio import Minio
from minio.error import S3Error


@deconstructible
class MinIOStorage(Storage):
    """
    MinIO Storage Base Class
    """

    def __init__(self, **settings_dict):
        # MinIO istemcisini oluştur
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_HTTPS,
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self.custom_domain = settings.MINIO_CUSTOM_DOMAIN
        self.use_https = settings.MINIO_USE_HTTPS

        # Bucket'ın var olduğundan emin ol
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Bucket'ın var olduğundan emin ol, yoksa oluştur"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"✓ MinIO bucket '{self.bucket_name}' oluşturuldu")
        except S3Error as e:
            print(f"✗ MinIO bucket kontrolü/oluşturma hatası: {e}")

    def _open(self, name, mode="rb"):
        """Dosyayı aç"""
        try:
            response = self.client.get_object(self.bucket_name, name)
            return BytesIO(response.read())
        except S3Error:
            raise FileNotFoundError(f"Dosya bulunamadı: {name}")

    def _save(self, name, content):
        """Dosyayı kaydet"""
        try:
            # İçeriği oku
            if hasattr(content, "read"):
                content_data = content.read()
            else:
                content_data = content

            # BytesIO nesnesine dönüştür
            if isinstance(content_data, str):
                content_data = content_data.encode("utf-8")

            content_io = BytesIO(content_data)

            # MinIO'ya yükle
            self.client.put_object(
                self.bucket_name,
                name,
                content_io,
                len(content_data),
            )

            return name
        except S3Error as e:
            raise Exception(f"Dosya kaydedilemedi: {e}")

    def delete(self, name):
        """Dosyayı sil"""
        try:
            self.client.remove_object(self.bucket_name, name)
        except S3Error:
            # Dosya zaten yoksa hata verme
            pass

    def exists(self, name):
        """Dosya var mı kontrol et"""
        try:
            self.client.stat_object(self.bucket_name, name)
            return True
        except S3Error:
            return False

    def size(self, name):
        """Dosya boyutunu al"""
        try:
            stat = self.client.stat_object(self.bucket_name, name)
            return stat.size
        except S3Error:
            raise FileNotFoundError(f"Dosya bulunamadı: {name}")

    def url(self, name):
        """Dosya URL'ini al"""
        # protocol = "https" if self.use_https else "http"
        return f"https://{self.custom_domain}/{name}"

    def listdir(self, path):
        """Dizin içeriğini listele"""
        if path and not path.endswith("/"):
            path += "/"

        directories = set()
        files = []

        try:
            objects = self.client.list_objects(self.bucket_name, prefix=path)
            for obj in objects:
                name = obj.object_name
                if name.startswith(path):
                    relative_name = name[len(path) :]
                    if "/" in relative_name:
                        # Alt dizin
                        dir_name = relative_name.split("/")[0]
                        directories.add(dir_name)
                    else:
                        # Dosya
                        files.append(relative_name)

        except S3Error:
            pass

        return list(directories), files


@deconstructible
class MinIOStaticStorage(MinIOStorage):
    """
    MinIO Static Files Storage
    """

    def __init__(self, **settings_dict):
        super().__init__(**settings_dict)
        self.location = settings.MINIO_STATIC_LOCATION

    def _save(self, name, content):
        """Static dosyayı kaydet"""
        # Static location prefix'i ekle
        full_name = f"{self.location}/{name}" if self.location else name
        print(f"🔧 Static dosya kaydediliyor: {name} -> {full_name}")
        super()._save(full_name, content)
        print(f"✅ Static dosya MinIO'ya yüklendi: {full_name}")
        # Orijinal dosya adını döndür (Django bunu bekler)
        return name

    def _open(self, name, mode="rb"):
        """Static dosyayı aç"""
        full_name = f"{self.location}/{name}" if self.location else name
        return super()._open(full_name, mode)

    def delete(self, name):
        """Static dosyayı sil"""
        full_name = f"{self.location}/{name}" if self.location else name
        return super().delete(full_name)

    def exists(self, name):
        """Static dosya var mı"""
        full_name = f"{self.location}/{name}" if self.location else name
        return super().exists(full_name)

    def size(self, name):
        """Static dosya boyutu"""
        full_name = f"{self.location}/{name}" if self.location else name
        return super().size(full_name)

    def url(self, name):
        """Static dosya URL'i"""
        if self.location:
            full_name = f"{self.location}/{name}"
        else:
            full_name = name
        return super().url(full_name)


@deconstructible
class MinIOMediaStorage(MinIOStorage):
    """
    MinIO Media Files Storage
    """

    def __init__(self, **settings_dict):
        super().__init__(**settings_dict)
        self.location = settings.MINIO_MEDIA_LOCATION

    def _save(self, name, content):
        """Media dosyayı kaydet"""
        # Media location prefix'i ekle ve Windows path separator'ını düzelt
        name = name.replace("\\", "/")
        full_name = f"{self.location}/{name}" if self.location else name
        print(f"🔧 Media dosya kaydediliyor: {name} -> {full_name}")
        super()._save(full_name, content)
        print(f"✅ Media dosya MinIO'ya yüklendi: {full_name}")
        # Orijinal dosya adını döndür (Django bunu bekler)
        return name

    def _open(self, name, mode="rb"):
        """Media dosyayı aç"""
        name = name.replace("\\", "/")
        full_name = f"{self.location}/{name}" if self.location else name
        return super()._open(full_name, mode)

    def delete(self, name):
        """Media dosyayı sil"""
        name = name.replace("\\", "/")
        full_name = f"{self.location}/{name}" if self.location else name
        return super().delete(full_name)

    def exists(self, name):
        """Media dosya var mı"""
        name = name.replace("\\", "/")
        full_name = f"{self.location}/{name}" if self.location else name
        return super().exists(full_name)

    def size(self, name):
        """Media dosya boyutu"""
        name = name.replace("\\", "/")
        full_name = f"{self.location}/{name}" if self.location else name
        return super().size(full_name)

    def url(self, name):
        """Media dosya URL'i"""
        name = name.replace("\\", "/")
        if self.location:
            full_name = f"{self.location}/{name}"
        else:
            full_name = name
        return super().url(full_name)
