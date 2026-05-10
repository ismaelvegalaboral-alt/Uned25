import base64
from pathlib import Path

from django.core.management.base import BaseCommand

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('ascii').rstrip('=')


class Command(BaseCommand):
    help = 'Genera claves VAPID para notificaciones push web.'

    def handle(self, *args, **options):
        base_dir = Path.cwd()
        private_path = base_dir / 'vapid_private.pem'

        private_key = ec.generate_private_key(ec.SECP256R1())
        public_numbers = private_key.public_key().public_numbers()

        x = public_numbers.x.to_bytes(32, 'big')
        y = public_numbers.y.to_bytes(32, 'big')
        public_key = b64url(b'\x04' + x + y)

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        private_path.write_bytes(private_pem)
        private_path.chmod(0o600)

        self.stdout.write(self.style.SUCCESS('Claves VAPID generadas correctamente.'))
        self.stdout.write('')
        self.stdout.write('Añade estas líneas a tu archivo .env:')
        self.stdout.write('')
        self.stdout.write('WEBPUSH_ENABLED=True')
        self.stdout.write(f'WEBPUSH_VAPID_PUBLIC_KEY={public_key}')
        self.stdout.write(f'WEBPUSH_VAPID_PRIVATE_KEY={private_path}')
        self.stdout.write('WEBPUSH_VAPID_SUB=mailto:ivegamkalpae@gmail.com')
