from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from .models import Patient

@receiver(post_save, sender=Patient)
def create_user_for_patient(sender, instance, created, **kwargs):

    if created and instance.user is None:

        username = f"p_{instance.id}"

        user = User.objects.create_user(
            username=username,
            password="123456"
        )

        instance.user = user
        instance.save()

        group, _ = Group.objects.get_or_create(name="Patient")
        user.groups.add(group)