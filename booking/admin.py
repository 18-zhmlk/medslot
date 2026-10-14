from django.contrib import admin

from .models import (
    ContactMessage,
    Doctor,
    Service,
    Slot,
    Appointment,
    PatientProfile
)


class AppointmentInline(admin.TabularInline):
    model = Appointment
    extra = 0

    fields = (
        "doctor",
        "service",
        "slot",
        "patient_name",
        "phone",
    )

    readonly_fields = (
        "doctor",
        "service",
        "slot",
        "patient_name",
        "phone",
    )


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):

    list_display = (
        "full_name",
        "iin",
        "phone",
        "user",
    )

    search_fields = (
        "full_name",
        "iin",
        "phone",
        "user__username",
    )

    def get_inline_instances(self, request, obj=None):
        if obj is None:
            return []

        class UserAppointmentsInline(admin.TabularInline):
            model = Appointment
            extra = 0

            fields = (
                "doctor",
                "service",
                "slot",
                "patient_name",
                "phone",
            )

            readonly_fields = (
                "doctor",
                "service",
                "slot",
                "patient_name",
                "phone",
            )

            def get_queryset(self, request):
                qs = super().get_queryset(request)

                return qs.filter(
                    user=self.instance.user
                ).select_related(
                    "doctor",
                    "service",
                    "slot"
                )

        inline = UserAppointmentsInline(self.model, self.admin_site)
        inline.instance = obj

        return [inline]


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "specialty",
    )

    search_fields = (
        "name",
        "specialty",
    )


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "doctor",
        "duration",
    )

    list_filter = (
        "doctor",
    )


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):

    list_display = (
        "doctor",
        "date",
        "time",
        "is_available",
    )

    list_filter = (
        "doctor",
        "is_available",
        "date",
    )


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):

    list_display = (
        "patient_name",
        "phone",
        "doctor",
        "service",
        "slot",
    )

    list_filter = (
        "doctor",
        "service",
    )

    search_fields = (
        "patient_name",
        "phone",
    )

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_info', 'created_at')
    search_fields = ('name', 'contact_info', 'message')
    readonly_fields = ('created_at',)