from django.contrib import admin
from users.models import User, UserConfirmation


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone_number', 'created_time')
    search_fields = ('username', 'email', 'phone_number', 'created_time')
    list_filter = ('username', 'email', 'phone_number', 'created_time')


admin.site.register(User, UserAdmin)
admin.site.register(UserConfirmation)
