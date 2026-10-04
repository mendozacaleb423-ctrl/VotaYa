import uuid
import qrcode

from io import BytesIO
from django.core.files import File
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from django.urls import reverse


class Votacion(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)

    # Usuario que crea y organiza la votación
    creador = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='votaciones',
        null=True,
        blank=True
    )

    # Código único y código QR de acceso
    codigo_acceso = models.CharField(
        max_length=10,
        unique=True,
        blank=True
    )

    qr_code = models.ImageField(
        upload_to='qr_codes/',
        blank=True,
        null=True
    )

    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def _str_(self):
        return self.titulo

    def esta_abierta(self):
        ahora = timezone.now()
        return (
            self.activa
            and self.fecha_inicio <= ahora
            and self.fecha_fin >= ahora
        )

    def save(self, *args, **kwargs):
        es_nueva = self.pk is None
        codigo_nuevo = not self.codigo_acceso

        if codigo_nuevo:
            self.codigo_acceso = uuid.uuid4().hex[:8].upper()

        generar_qr = es_nueva or codigo_nuevo or not self.qr_code

        if generar_qr:
            ruta = reverse(
                'elecciones:votar_participante',
                kwargs={'codigo': self.codigo_acceso}
            )

            # En producción se debe configurar un dominio público.
            # En desarrollo, esta dirección sirve solo en la computadora.
            dominio = getattr(
                settings,
                'URL_PUBLICA',
                'http://127.0.0.1:8000'
            ).rstrip('/')

            url_voto = f'{dominio}{ruta}'

            qr = qrcode.QRCode(
                version=1,
                box_size=10,
                border=5
            )
            qr.add_data(url_voto)
            qr.make(fit=True)

            imagen = qr.make_image(
                fill_color='black',
                back_color='white'
            )

            buffer = BytesIO()
            imagen.save(buffer, format='PNG')
            buffer.seek(0)

            self.qr_code.save(
                f'qr_{self.codigo_acceso}.png',
                File(buffer),
                save=False
            )

        super().save(*args, **kwargs)


class Opcion(models.Model):
    votacion = models.ForeignKey(
        Votacion,
        on_delete=models.CASCADE,
        related_name='opciones'
    )

    texto = models.CharField(max_length=200)

    def _str_(self):
        return self.texto


class Voto(models.Model):
    # Usuarios registrados y participantes anónimos
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='votos'
    )

    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True
    )

    votacion = models.ForeignKey(
        Votacion,
        on_delete=models.CASCADE,
        related_name='votos'
    )

    opcion = models.ForeignKey(
        Opcion,
        on_delete=models.CASCADE,
        related_name='votos'
    )

    fecha_voto = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        if self.usuario:
            usuario_str = self.usuario.username
        else:
            clave = self.session_key[:6] if self.session_key else ''
            usuario_str = f'Anónimo ({clave})'

        return f'{usuario_str} - {self.votacion.titulo}'