from django.contrib import admin
from messaging.models import ChatMessage
from messaging.models import ChatThread
from messaging.models import MessageRead

admin.site.register(ChatThread)
admin.site.register(ChatMessage)
admin.site.register(MessageRead)
