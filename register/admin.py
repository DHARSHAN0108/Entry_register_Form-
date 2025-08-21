from django.contrib import admin
from .models import Entry, ReceptionistUserAuth


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "phone",
        "category",
        "reason",
        "appointment_date",
        "appointment_time",
        "designated_attendee",
        "document",
    )
    list_filter = ("appointment_date", "category", "designated_attendee")
    search_fields = ("name", "email", "phone")


@admin.register(ReceptionistUserAuth)
class ReceptionistUserAuthAdmin(admin.ModelAdmin):
    list_display = ("username", "is_approved", "created_at")
    list_filter = ("is_approved", "created_at")
    search_fields = ("username",)
    actions = ["approve_selected"]

    @admin.action(description="Approve selected receptionists")
    def approve_selected(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"Approved {updated} receptionist(s).")
