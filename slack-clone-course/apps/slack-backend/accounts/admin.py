from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    # A plain ModelAdmin (not django's UserAdmin) keeps things simple with our
    # email-based login. Good enough for a dev/admin console.
    list_display = ("username", "email", "is_staff", "last_seen")
    search_fields = ("username", "email")
