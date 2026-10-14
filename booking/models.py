from django.db import models
from django.contrib.auth.models import User


class Doctor(models.Model):
    name = models.CharField(max_length=100)
    specialty = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} — {self.specialty}"


class Service(models.Model):
    doctor = models.ForeignKey(
        Doctor,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=150)
    duration = models.PositiveIntegerField()

    def __str__(self):
        if self.doctor:
            return f"{self.name} — {self.doctor.name}"
        return self.name


class Slot(models.Model):
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE
    )
    date = models.DateField()
    time = models.TimeField()
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.doctor.name} — {self.date} {self.time}"


class Appointment(models.Model):
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    patient_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE
    )

    slot = models.OneToOneField(
        Slot,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.patient_name} — {self.slot}"


class PatientProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    iin = models.CharField(
        max_length=12,
        unique=True
    )

    full_name = models.CharField(
        max_length=150
    )

    phone = models.CharField(
        max_length=20,
        unique=True
    )

    def __str__(self):
        return f"{self.full_name} — {self.iin}"

class ContactMessage(models.Model):
    name = models.CharField(max_length=100, verbose_name="Имя")
    contact_info = models.CharField(max_length=150, verbose_name="Email или Телефон")
    message = models.TextField(verbose_name="Сообщение")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата отправки")

    def __str__(self):
        return f"{self.name} ({self.contact_info})"

    class Meta:
        verbose_name = "Сообщение обратной связи"
        verbose_name_plural = "Сообщения обратной связи"