from django import forms
from .models import MainClinic, SubClinic, Visit, Patient, Doctor,Appointment

# ==================== نموذج المرضى ====================
class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['name', 'age', 'gender', 'phone', 'has_chronic', 'chronic_diseases']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'has_chronic': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'chronic_diseases': forms.TextInput(attrs={'class': 'form-control'}),
        }

# ==================== نموذج الدكاترة ====================
# أيام العمل
DAYS_CHOICES = [
    ('السبت', 'السبت'),
    ('الأحد', 'الأحد'),
    ('الاثنين', 'الاثنين'),
    ('الثلاثاء', 'الثلاثاء'),
    ('الأربعاء', 'الأربعاء'),
    ('الخميس', 'الخميس'),
    ('الجمعة', 'الجمعة'),
]


class DoctorForm(forms.ModelForm):

    # بنعرّفهم في الفورم فقط (مش في الموديل)
    working_days = forms.MultipleChoiceField(
        choices=DAYS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label="أيام العمل"
    )

    working_hours = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'مثال: 09:00 ص - 01:00 م'
        }),
        label="ساعات العمل"
    )

    class Meta:
        model = Doctor
        fields = ['name', 'sub_clinic']  # فقط الموجود في الموديل
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم الطبيب'
            }),
            'sub_clinic': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    # تحويل بيانات الفورم → الموديل
    def save(self, commit=True):
        instance = super().save(commit=False)

        # نقل البيانات من الفورم للموديل
        instance.working_days = self.cleaned_data['working_days']
        instance.working_hours = self.cleaned_data['working_hours']

        if commit:
            instance.save()

        return instance

# ==================== نموذج الزيارات ====================
class VisitForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = ['patient', 'main_clinic', 'sub_clinic', 'doctor', 'analysis_results', 'medicines']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'main_clinic': forms.Select(attrs={'class': 'form-control'}),
            'sub_clinic': forms.Select(attrs={'class': 'form-control'}),
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'analysis_results': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'تشخيص حالة المريض'}),
            'medicines': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'الأدوية الموصوفة'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # لو في instance اختارنا عيادة فرعية
        if self.instance and self.instance.sub_clinic:
            self.fields['doctor'].queryset = Doctor.objects.filter(sub_clinic=self.instance.sub_clinic)
        else:
            self.fields['doctor'].queryset = Doctor.objects.all()

# ==================== نموذج العيادات ====================
class MainClinicForm(forms.ModelForm):
    class Meta:
        model = MainClinic
        fields = ['name']
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control'})}

class SubClinicForm(forms.ModelForm):
    class Meta:
        model = SubClinic
        fields = ['main_clinic', 'name']
        widgets = {
            'main_clinic': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = '__all__'

        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'main_clinic': forms.Select(attrs={'class': 'form-control'}),
            'sub_clinic': forms.Select(attrs={'class': 'form-control'}),
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'day': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }