from django.contrib import admin

from .models import Attachment, Channel, ChannelMember, Message, Reaction

admin.site.register(Channel)
admin.site.register(ChannelMember)
admin.site.register(Message)
admin.site.register(Reaction)
admin.site.register(Attachment)
