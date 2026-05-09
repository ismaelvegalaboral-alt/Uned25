from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from vacations.permissions import PLATFORM_GROUPS


class Command(BaseCommand):
    help = 'Crea los grupos base de Kalpae Gestión de Ausencias y, opcionalmente, asigna un usuario a un rol.'

    def add_arguments(self, parser):
        parser.add_argument('--username', help='Usuario al que asignar un rol.')
        parser.add_argument('--role', choices=PLATFORM_GROUPS, help='Rol a asignar al usuario indicado.')
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Elimina otros roles de plataforma del usuario antes de asignar el nuevo.',
        )

    def handle(self, *args, **options):
        groups = {name: Group.objects.get_or_create(name=name)[0] for name in PLATFORM_GROUPS}
        self.stdout.write(self.style.SUCCESS('Grupos creados/verificados: ' + ', '.join(groups)))

        username = options.get('username')
        role = options.get('role')
        if not username and not role:
            return
        if not username or not role:
            raise CommandError('Debes indicar --username y --role juntos.')

        User = get_user_model()
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist as exc:
            raise CommandError(f'No existe el usuario {username!r}.') from exc

        if options.get('clear_existing'):
            for group in groups.values():
                user.groups.remove(group)

        user.groups.add(groups[role])
        self.stdout.write(self.style.SUCCESS(f'Usuario {username!r} asignado al rol {role!r}.'))
