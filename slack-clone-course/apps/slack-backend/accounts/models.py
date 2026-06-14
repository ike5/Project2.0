"""
Custom user model.

We define a custom User *now*, before the first migration, because switching
AUTH_USER_MODEL after tables exist is extremely painful. We log in with **email**
(Slack does), so email is unique and is the USERNAME_FIELD; `username` is the
display handle used for @mentions.
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Manager that creates users by email instead of username."""

    use_in_migrations = True

    def _create_user(self, email, username, password, **extra):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, username, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, username, password, **extra)

    def create_superuser(self, email, username, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self._create_user(email, username, password, **extra)


class User(AbstractUser):
    email = models.EmailField(unique=True)
    # Profile bits used by the UI (Module 10).
    display_name = models.CharField(max_length=80, blank=True)
    avatar_url = models.URLField(blank=True)
    # Presence is tracked in Redis (Module 06); this is just a fallback last-seen.
    last_seen = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]   # prompted by createsuperuser besides email

    objects = UserManager()

    def __str__(self):
        return self.username
