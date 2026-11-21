from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from tracker.models import Budget, Transaction


class Command(BaseCommand):
    help = "Give transactions and budgets that have no owner (created before login existed) to one user."

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username=options["username"])
        except User.DoesNotExist:
            raise CommandError(f"No user called {options['username']!r}.")
        tx = Transaction.objects.filter(user__isnull=True).update(user=user)
        bud = Budget.objects.filter(user__isnull=True).update(user=user)
        self.stdout.write(self.style.SUCCESS(f"Assigned {tx} transactions and {bud} budgets to {user.username}."))
