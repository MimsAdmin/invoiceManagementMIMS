# authen/models.py
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

class Profile(models.Model):
    APPROVAL_CHOICES = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="profile"
    )
    approval_status = models.CharField(
        max_length=9, 
        choices=APPROVAL_CHOICES, 
        default="PENDING"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.approval_status}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


@receiver(post_save, sender=User)
def ensure_profile(sender, instance, created, **kwargs):
    """Ensure every user has a profile"""
    if created:
        Profile.objects.create(user=instance)
    else:
        Profile.objects.get_or_create(user=instance)


@receiver(pre_save, sender=Profile)
def auto_activate_on_approval(sender, instance, **kwargs):

    if instance.pk:  # Only for existing profiles
        try:
            old_instance = Profile.objects.get(pk=instance.pk)
            # Check if approval_status changed
            if old_instance.approval_status != instance.approval_status:
                if instance.approval_status == "APPROVED":
                    instance.user.is_active = True
                    instance.user.save(update_fields=['is_active'])
                elif instance.approval_status == "REJECTED":
                    instance.user.is_active = False
                    instance.user.save(update_fields=['is_active'])
        except Profile.DoesNotExist:
            pass
    else:  # New profile
        if instance.approval_status == "APPROVED":
            instance.user.is_active = True
            instance.user.save(update_fields=['is_active'])