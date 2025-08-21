from django.db import models

CATEGORY_CHOICES = [
    ('student', 'Student'),
    ('staff', 'Staff'),
    ('employee', 'Employee'),
    ('intern', 'Intern'),
]

ATTENDEE_CHOICES = [
    ('member1', 'Member 1'),
    ('member2', 'Member 2'),
]

STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('rescheduled', 'Rescheduled'),
]

class Entry(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=10)
    reason = models.TextField()
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    designated_attendee = models.CharField(max_length=50, choices=ATTENDEE_CHOICES)
    document = models.FileField(upload_to='documents/', blank=True, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    reschedule_token = models.CharField(max_length=100, blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} — {self.appointment_date} {self.appointment_time}"

    class Meta:
        ordering = ['-created_at']

class ReceptionistUserAuth(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)  # hashed password
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'receptionistuserauth'

    def __str__(self):
        return self.username