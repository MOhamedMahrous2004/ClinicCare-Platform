from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from clinics.models import Doctor

class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        doctor_group, _ = Group.objects.get_or_create(name='Doctor')

        doctors = Doctor.objects.all()

        for doctor in doctors:

            if doctor.user:
                self.stdout.write(f"Skipped {doctor.name} (already linked)")
                continue

            username = doctor.name.replace(" ", "_").lower()

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": doctor.name,
                }
            )

            if created:
                user.set_password("1234")
                user.save()


            user.groups.add(doctor_group)


            if Doctor.objects.filter(user=user).exclude(id=doctor.id).exists():
                self.stdout.write(f"Skipped {doctor.name} (user already assigned)")
                continue

            doctor.user = user
            doctor.save()

            self.stdout.write(
                self.style.SUCCESS(f"Linked {doctor.name} -> {user.username}")
            )