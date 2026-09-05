from django.db import models
from django.contrib.auth.models import User

# -------------------- العيادات --------------------
class MainClinic(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class SubClinic(models.Model):
    main_clinic = models.ForeignKey(MainClinic, on_delete=models.CASCADE, related_name='sub_clinics')
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.main_clinic.name})"


# -------------------- المستخدمين --------------------

class Patient(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='patient_account'
    )


    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_patients'
    )

    GENDER_CHOICES = [
        ('M', 'ذكر'),
        ('F', 'أنثى'),
    ]

    name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=20)

    has_chronic = models.BooleanField(default=False)
    chronic_diseases = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    name = models.CharField(max_length=100)
    sub_clinic = models.ForeignKey(SubClinic, on_delete=models.CASCADE)

    working_days = models.CharField(max_length=100, blank=True, null=True)
    working_hours = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.sub_clinic.name})"


# -------------------- الحجوزات --------------------
class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)

    main_clinic = models.ForeignKey(MainClinic, on_delete=models.CASCADE)
    sub_clinic = models.ForeignKey(SubClinic, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)

    day = models.CharField(max_length=20)
    date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient} - {self.doctor} - {self.date}"


# -------------------- الزيارات --------------------
class Visit(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE)  # اللي سجل الزيارة

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)

    main_clinic = models.ForeignKey(MainClinic, on_delete=models.SET_NULL, null=True)
    sub_clinic = models.ForeignKey(SubClinic, on_delete=models.SET_NULL, null=True)

    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True)

    analysis_results = models.TextField(blank=True, null=True)
    medicines = models.TextField(blank=True, null=True)

    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.name} - {self.doctor.name if self.doctor else 'No Doctor'}"


# -------------------- ملفات الزيارات --------------------
class VisitFile(models.Model):
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='visits/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File for {self.visit.patient.name}"

    def is_pdf(self):
        return self.file.name.lower().endswith('.pdf')