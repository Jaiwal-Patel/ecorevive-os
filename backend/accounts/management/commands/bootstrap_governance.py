import secrets

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import User, UserRole
from audit.services import record_event


class Command(BaseCommand):
    help = "Create or repair Founder Guardian and optional disclosed Founder Recovery identities."

    def add_arguments(self, parser):
        parser.add_argument("--founder-email", default=settings.FOUNDER_EMAIL)
        parser.add_argument("--founder-name", default="Jaiwal Patel")
        parser.add_argument("--recovery-email", default="")
        parser.add_argument("--recovery-name", default="EcoRevive Founder Recovery")
        parser.add_argument("--temporary-password", default="")

    @transaction.atomic
    def handle(self, *args, **options):
        founder_email = options["founder_email"].strip().lower()
        if not founder_email:
            raise CommandError("Founder email is required.")

        password = options["temporary_password"] or secrets.token_urlsafe(18)
        founder, created = User.objects.get_or_create(
            email=founder_email,
            defaults={
                "full_name": options["founder_name"],
                "role": UserRole.FOUNDER_GUARDIAN,
                "is_staff": True,
                "is_superuser": True,
                "must_change_password": True,
            },
        )
        if created:
            founder.set_password(password)
            founder.save(allow_governance_update=True)
            record_event(
                actor=founder,
                event_type="governance.founder_created",
                summary="Created Founder Guardian identity",
                object_type="User",
                object_id=founder.id,
            )
        else:
            changed = False
            if founder.role != UserRole.FOUNDER_GUARDIAN:
                founder.role = UserRole.FOUNDER_GUARDIAN
                changed = True
            if not founder.is_staff or not founder.is_superuser or not founder.is_active:
                founder.is_staff = True
                founder.is_superuser = True
                founder.is_active = True
                changed = True
            if options["temporary_password"]:
                founder.set_password(password)
                founder.must_change_password = True
                changed = True
            if changed:
                founder.save(allow_governance_update=True)

        self.stdout.write(self.style.SUCCESS(f"Founder Guardian ready: {founder.email}"))
        if created or options["temporary_password"]:
            self.stdout.write(f"Temporary password: {password}")

        recovery_email = options["recovery_email"].strip().lower()
        if not recovery_email:
            self.stdout.write(self.style.WARNING(
                "Founder Recovery was not created. Run again with --recovery-email using a separate secured mailbox."
            ))
            return
        if recovery_email == founder_email:
            raise CommandError("Recovery email must differ from Founder Guardian email.")

        recovery_password = secrets.token_urlsafe(24)
        recovery, recovery_created = User.objects.get_or_create(
            email=recovery_email,
            defaults={
                "full_name": options["recovery_name"],
                "role": UserRole.FOUNDER_RECOVERY,
                "must_change_password": True,
            },
        )
        if recovery_created:
            recovery.set_password(recovery_password)
            recovery.save(allow_governance_update=True)
            record_event(
                actor=founder,
                event_type="governance.recovery_created",
                summary="Created disclosed Founder Recovery identity",
                object_type="User",
                object_id=recovery.id,
            )
        elif recovery.role != UserRole.FOUNDER_RECOVERY:
            recovery.role = UserRole.FOUNDER_RECOVERY
            recovery.save(allow_governance_update=True)

        self.stdout.write(self.style.SUCCESS(f"Founder Recovery ready: {recovery.email}"))
        if recovery_created:
            self.stdout.write(f"Founder Recovery temporary password: {recovery_password}")
