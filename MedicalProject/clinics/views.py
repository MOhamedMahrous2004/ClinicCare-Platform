from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.db.models.functions import TruncMonth
from django.contrib import messages
from django.contrib.auth.decorators import login_required , user_passes_test
from django.http import HttpResponse, JsonResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from django.core.paginator import Paginator
from .models import MainClinic, SubClinic, Visit, Patient, VisitFile, Doctor,Appointment
from .forms import MainClinicForm, SubClinicForm, VisitForm, PatientForm, DoctorForm,AppointmentForm
from rest_framework.response import Response
from .serializers import PatientSerializer, VisitSerializer, MainClinicSerializer, SubClinicSerializer, DoctorSerializer
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from datetime import date, timedelta
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm


def is_admin(user):
    return (
        user.is_superuser or
        user.groups.filter(name='Admin').exists()
    )

def can_manage_visits(user):
    return (
        user.is_superuser or
        user.groups.filter(name='Admin').exists() or
        user.groups.filter(name='Nurse').exists() or
        user.groups.filter(name='Doctor').exists()
    )

def is_admin_or_nurse(user):
    return (
        user.is_superuser or
        user.groups.filter(name='Admin').exists() or
        user.groups.filter(name='Nurse').exists()
    )

def is_doctor(user):
    return (
        user.is_superuser or
        user.groups.filter(name='Doctor').exists()
    )

def is_patient(user):
    return user.groups.filter(name='Patient').exists()

def get_visits_queryset(user):
    qs = Visit.objects.select_related('patient', 'doctor', 'main_clinic', 'sub_clinic').all()

    if is_admin_or_nurse(user):
        return qs

    if is_doctor(user):
        return qs.filter(doctor__user=user)

    if is_patient(user):
        return qs.filter(patient__user=user)

    return Visit.objects.none()


def get_appointments_queryset(user):
    qs = Appointment.objects.select_related('patient', 'doctor', 'main_clinic', 'sub_clinic').all()

    if is_admin_or_nurse(user):
        return qs

    if is_doctor(user):
        return qs.filter(doctor__user=user)

    if is_patient(user):
        return qs.filter(patient__user=user)

    return Appointment.objects.none()




def register_view(request):
    form = UserCreationForm(request.POST or None)

    if form.is_valid():
        user = form.save()


        patient_group, _ = Group.objects.get_or_create(name='Patient')
        user.groups.add(patient_group)

        messages.success(request, "✅ تم إنشاء الحساب بنجاح")
        return redirect('login')

    return render(request, 'clinics/register.html', {'form': form})

# -------------------- الصفحة الرئيسية --------------------
@login_required

def home_view(request):
    return render(request, 'clinics/home.html', {
        'patients_count': Patient.objects.count(),
        'clinics_count': MainClinic.objects.count(),
        'visits_count': Visit.objects.count(),
    })

# -------------------- Dashboard --------------------

@login_required
@user_passes_test(is_admin)
def dashboard_view(request):

    # 📊 عدد الزيارات شهريًا
    visits_by_month = (
        Visit.objects
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    months = [v['month'].strftime('%Y-%m') for v in visits_by_month]
    counts = [v['count'] for v in visits_by_month]

    # 🏥 العيادات
    clinics_data = Visit.objects.values('main_clinic__name').annotate(count=Count('id')).order_by('-count')
    clinic_names = [c['main_clinic__name'] or "غير محدد" for c in clinics_data]
    clinic_counts = [c['count'] for c in clinics_data]

    # 👨‍⚕️ الدكاترة
    doctors_data = (
        Visit.objects
        .values('doctor__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    doctor_names = [d['doctor__name'] or "غير محدد" for d in doctors_data]
    doctor_counts = [d['count'] for d in doctors_data]

    # 👥 المرضى
    patients_data = Patient.objects.values('gender').annotate(count=Count('id'))
    gender_labels = []
    gender_counts = []

    for p in patients_data:
        if p['gender'] == 'M':
            gender_labels.append('ذكور')
        elif p['gender'] == 'F':
            gender_labels.append('إناث')
        else:
            gender_labels.append('غير محدد')
        gender_counts.append(p['count'])

    # 📅 الحجوزات (عدد)
    appointments_count = Appointment.objects.count()

    # 📅 الحجوزات شهريًا
    appointments_by_month = (
        Appointment.objects
        .annotate(month=TruncMonth('date'))  # لو اسم الحقل مختلف غيّره هنا
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    appointments_months = [a['month'].strftime('%Y-%m') for a in appointments_by_month]
    appointments_counts = [a['count'] for a in appointments_by_month]

    return render(request, 'clinics/dashboard.html', {
        'patients_count': Patient.objects.count(),
        'clinics_count': MainClinic.objects.count(),
        'visits_count': Visit.objects.count(),

        'months': months,
        'counts': counts,

        'clinic_names': clinic_names,
        'clinic_counts': clinic_counts,

        'doctor_names': doctor_names,
        'doctor_counts': doctor_counts,

        'gender_labels': gender_labels,
        'gender_counts': gender_counts,

        # 🆕 الحجوزات
        'appointments_count': appointments_count,
        'appointments_months': appointments_months,
        'appointments_counts': appointments_counts,
    })

# ==================== المرضى ====================
@login_required
def patients_list_view(request):

    query = request.GET.get('q', '')

    # ================= ROLE FILTER =================
    if request.user.is_superuser or request.user.groups.filter(name='Admin').exists():

        patients = Patient.objects.all()

    elif is_patient(request.user):

        patients = Patient.objects.filter(user=request.user)

    elif is_doctor(request.user) or request.user.groups.filter(name='Nurse').exists():

        patients = Patient.objects.filter(created_by=request.user)

    else:

        patients = Patient.objects.none()

    # ================= SEARCH =================
    if query:
        patients = patients.filter(
            Q(name__icontains=query) |
            Q(phone__icontains=query)
        )

    # ================= PAGINATION =================
    paginator = Paginator(patients, 10)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    return render(request, 'clinics/users_list.html', {
        'users': page_obj,
        'query': query
    })

@login_required
def patient_create_view(request):

    form = PatientForm(request.POST or None)

    if form.is_valid():
        patient = form.save(commit=False)

        # ================= PATIENT USER =================
        if request.user.groups.filter(name='Patient').exists():

            if Patient.objects.filter(user=request.user).exists():
                messages.error(request, "❌ مسموح لك بمريض واحد فقط")
                return redirect('patients_list')

            patient.user = request.user

        else:
            patient.user = None

        # ✅ مين أنشأ المريض
        patient.created_by = request.user

        patient.save()

        messages.success(request, '✅ تم إضافة المريض')
        return redirect('patients_list')

    return render(request, 'clinics/user_create.html', {'form': form})

@login_required

def patient_edit_view(request, id):
    patient = get_object_or_404(Patient, id=id)
    form = PatientForm(request.POST or None, instance=patient)
    if form.is_valid():
        form.save()
        messages.success(request, '✅ تم تعديل المريض')
        return redirect('patients_list')
    return render(request, 'clinics/user_create.html', {'form': form, 'is_edit': True})

@login_required

def patient_delete_view(request, id):
    patient = get_object_or_404(Patient, id=id)
    patient.delete()
    messages.warning(request, '⚠️ تم حذف المريض')
    return redirect('patients_list')

# ==================== العيادات ====================
@login_required
@user_passes_test(is_admin)
def clinics_list_view(request):
    query = request.GET.get('q', '')
    main_clinics = MainClinic.objects.prefetch_related('sub_clinics')
    if query:
        main_clinics = main_clinics.filter(
            Q(name__icontains=query) | Q(sub_clinics__name__icontains=query)
        ).distinct()
    return render(request, 'clinics/clinics_list.html', {'main_clinics': main_clinics, 'query': query})

@login_required
@user_passes_test(is_admin)
def main_clinic_add_view(request):
    form = MainClinicForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('clinics_list')
    return render(request, 'clinics/main_clinic_add.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def sub_clinic_add_view(request):
    form = SubClinicForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('clinics_list')
    return render(request, 'clinics/sub_clinic_add.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def edit_main_clinic_view(request, id):
    clinic = get_object_or_404(MainClinic, id=id)
    form = MainClinicForm(request.POST or None, instance=clinic)
    if form.is_valid():
        form.save()
        return redirect('clinics_list')
    return render(request, 'clinics/edit_main_clinic.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def delete_main_clinic_view(request, id):
    clinic = get_object_or_404(MainClinic, id=id)
    clinic.delete()
    return redirect('clinics_list')

@login_required
@user_passes_test(is_admin)
def edit_sub_clinic_view(request, id):
    sub = get_object_or_404(SubClinic, id=id)
    form = SubClinicForm(request.POST or None, instance=sub)
    if form.is_valid():
        form.save()
        return redirect('clinics_list')
    return render(request, 'clinics/edit_sub_clinic.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def delete_sub_clinic_view(request, id):
    sub = get_object_or_404(SubClinic, id=id)
    sub.delete()
    return redirect('clinics_list')

# ===================== الدكاترة ===================
@login_required
@user_passes_test(is_admin)
def doctor_list_view(request):
    doctors = Doctor.objects.select_related('sub_clinic__main_clinic').all()


    search = request.GET.get('search')
    if search:
        doctors = doctors.filter(name__icontains=search)


    main_clinic = request.GET.get('main_clinic')
    if main_clinic:
        doctors = doctors.filter(sub_clinic__main_clinic_id=main_clinic)


    sub_clinic = request.GET.get('sub_clinic')
    if sub_clinic:
        doctors = doctors.filter(sub_clinic_id=sub_clinic)

    context = {
        'doctors': doctors,
        'main_clinics': MainClinic.objects.all(),
        'sub_clinics': SubClinic.objects.all(),
    }

    return render(request, 'clinics/doctor_list.html', context)


@login_required
@user_passes_test(is_admin)
def doctor_edit_view(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    if request.method == 'POST':
        form = DoctorForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            return redirect('doctor_list')
    else:
        form = DoctorForm(instance=doctor)
    return render(request, 'clinics/doctor_edit.html', {'form': form, 'doctor': doctor})

@login_required
@user_passes_test(is_admin)
def doctor_delete_view(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    if request.method == 'POST':
        doctor.delete()
        return redirect('doctor_list')

@login_required
@user_passes_test(is_admin)
def doctor_create_view(request):
    form = DoctorForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, '✅ تم إضافة الطبيب بنجاح')
        return redirect('doctor_list')  # رابط قائمة الأطباء
    return render(request, 'clinics/doctor_create.html', {'form': form})

@login_required

def doctor_available_days(request):
    doctor_id = request.GET.get("doctor_id")

    if not doctor_id:
        return JsonResponse({"disabled_days": []})

    doctor = Doctor.objects.get(id=doctor_id)

    # تحويل الأيام من النص
    days = (doctor.working_days or "").replace("و", ",").split(",")
    days = [d.strip() for d in days if d.strip()]

    # تحويل لأرقام الأسبوع (Flatpickr)
    mapping = {
        "السبت": 6,
        "الأحد": 0,
        "الاثنين": 1,
        "الثلاثاء": 2,
        "الأربعاء": 3,
        "الخميس": 4,
        "الجمعة": 5,
    }

    disabled = []
    for k, v in mapping.items():
        if k not in days:
            disabled.append(v)

    return JsonResponse({
        "disabled_days": disabled
    })

# ==================== الحجوزات ====================

@login_required

def extract_days(days_text):
    return [d.strip() for d in days_text.replace('و', ',').split(',')]

@login_required

def extract_hours(hours_text):
    try:
        parts = hours_text.split('-')
        return parts[0].strip(), parts[1].strip()
    except:
        return "", ""

@login_required
def create_appointment(request):

    # ================= ROLE FILTER =================
    if request.user.is_superuser or request.user.groups.filter(name='Admin').exists():

        patients = Patient.objects.all()

    elif is_patient(request.user):

        patients = Patient.objects.filter(user=request.user)

    elif is_doctor(request.user) or request.user.groups.filter(name='Nurse').exists():

        patients = Patient.objects.filter(created_by=request.user)

    else:

        patients = Patient.objects.none()

    main_clinics = MainClinic.objects.all()

    if request.method == "POST":

        patient_id = request.POST.get('patient')
        main_clinic_id = request.POST.get('main_clinic')
        sub_clinic_id = request.POST.get('sub_clinic')
        doctor_id = request.POST.get('doctor')
        selected_day = request.POST.get('day')
        selected_date = request.POST.get('date')

        if not patient_id or not doctor_id or not selected_day or not selected_date:
            messages.error(request, "❌ لازم تملا كل البيانات")
            return redirect('create_appointment')

        # منع التكرار
        duplicate = Appointment.objects.filter(
            doctor_id=doctor_id,
            patient_id=patient_id,
            date=selected_date
        ).exists()

        if duplicate:
            messages.error(request, "❌ المريض حجز بالفعل مع نفس الدكتور في هذا اليوم")
            return redirect('create_appointment')

        # الحد الأقصى
        count = Appointment.objects.filter(
            doctor_id=doctor_id,
            date=selected_date
        ).count()

        if count >= 20:
            messages.error(request, "❌ اليوم ده فل (20 حجز)")
            return redirect('create_appointment')

        Appointment.objects.create(
            patient_id=patient_id,
            main_clinic_id=main_clinic_id,
            sub_clinic_id=sub_clinic_id,
            doctor_id=doctor_id,
            day=selected_day,
            date=selected_date
        )

        messages.success(request, "✅ تم الحجز بنجاح")

        return redirect('create_appointment')

    return render(request, 'clinics/create_appointment.html', {
        'patients': patients,
        'main_clinics': main_clinics
    })

@login_required

def validate_doctor_day(doctor, day):
    days = (doctor.working_days or "").replace("و", ",").split(",")
    days = [d.strip() for d in days]
    return day in days

@login_required

def doctor_available_days(request):
    doctor_id = request.GET.get("doctor_id")

    if not doctor_id:
        return JsonResponse({"allowed_days": []})

    doctor = Doctor.objects.get(id=doctor_id)

    working_days = (doctor.working_days or "").replace("و", ",").split(",")
    working_days = [d.strip() for d in working_days]

    # تحويل عربي → رقم يوم
    days_map = {
        "السبت": 5,
        "الأحد": 6,
        "الاثنين": 0,
        "الثلاثاء": 1,
        "الأربعاء": 2,
        "الخميس": 3,
        "الجمعة": 4,
    }

    allowed_days_numbers = [days_map[d] for d in working_days if d in days_map]

    available_dates = []

    today = date.today()

    for i in range(30):
        d = today + timedelta(days=i)

        if d.weekday() in allowed_days_numbers:

            count = Appointment.objects.filter(
                doctor_id=doctor_id,
                date=d
            ).count()

            if count < 20:
                available_dates.append(d.strftime("%Y-%m-%d"))

    return JsonResponse({
        "available_dates": available_dates
    })


@login_required
def appointments_list_view(request):

    appointments = Appointment.objects.select_related(
        'doctor',
        'patient',
        'main_clinic',
        'sub_clinic'
    )

    # ================= ROLE FILTER =================
    if is_admin_or_nurse(request.user):
        pass

    elif is_doctor(request.user):
        appointments = appointments.filter(doctor__user=request.user)

    elif is_patient(request.user):
        appointments = appointments.filter(patient__user=request.user)

    else:
        appointments = Appointment.objects.none()

    # ================= FILTERS =================
    doctor = request.GET.get('doctor')
    main_clinic = request.GET.get('main_clinic')
    sub_clinic = request.GET.get('sub_clinic')
    patient = request.GET.get('patient')
    day = request.GET.get('day')
    search = request.GET.get('search')

    if is_admin_or_nurse(request.user):

        if doctor:
            appointments = appointments.filter(doctor_id=doctor)

        if main_clinic:
            appointments = appointments.filter(main_clinic_id=main_clinic)

        if sub_clinic:
            appointments = appointments.filter(sub_clinic_id=sub_clinic)

        if patient:
            appointments = appointments.filter(patient_id=patient)

    if day:
        appointments = appointments.filter(day__icontains=day)

    if search:
        appointments = appointments.filter(
            Q(doctor__name__icontains=search) |
            Q(patient__name__icontains=search) |
            Q(main_clinic__name__icontains=search) |
            Q(sub_clinic__name__icontains=search)
        )

    paginator = Paginator(appointments, 10)
    page_number = request.GET.get('page')
    appointments = paginator.get_page(page_number)

    return render(request, 'clinics/appointments_list.html', {
        'appointments': appointments,
        'doctors': Doctor.objects.all(),
        'main_clinics': MainClinic.objects.all(),
        'sub_clinics': SubClinic.objects.all(),
        'patients': Patient.objects.all(),

        'selected_doctor': doctor,
        'selected_patient': patient,
        'selected_main': main_clinic,
        'selected_sub': sub_clinic,
        'selected_day': day,
        'search_value': search,
    })

@login_required

def edit_appointment(request, id):
    appointment = Appointment.objects.get(id=id)

    patients = Patient.objects.all()
    main_clinics = MainClinic.objects.all()

    if request.method == "POST":

        appointment.patient_id = request.POST.get('patient')
        appointment.main_clinic_id = request.POST.get('main_clinic')
        appointment.sub_clinic_id = request.POST.get('sub_clinic')
        appointment.doctor_id = request.POST.get('doctor')
        appointment.day = request.POST.get('day')
        appointment.date = request.POST.get('date')

        appointment.save()

        messages.success(request, "✅ تم تعديل الحجز بنجاح")
        return redirect('appointments_list')

    return render(request, 'clinics/edit_appointment.html', {
        'appointment': appointment,
        'patients': patients,
        'main_clinics': main_clinics
    })

@login_required

def delete_appointment(request, id):
    appointment = Appointment.objects.get(id=id)
    appointment.delete()

    messages.success(request, "🗑️ تم حذف الحجز بنجاح")
    return redirect('appointments_list')

# ==================== الزيارات ====================
@login_required
def visit_list_view(request):

    query = request.GET.get('q', '')
    main_clinic_id = request.GET.get('main_clinic')
    sub_clinic_id = request.GET.get('sub_clinic')

    visits = Visit.objects.select_related(
        'patient',
        'doctor',
        'main_clinic',
        'sub_clinic'
    )

    # ================= ROLE FILTER =================
    if is_admin_or_nurse(request.user):
        pass

    elif is_doctor(request.user):
        visits = visits.filter(doctor__user=request.user)

    elif is_patient(request.user):
        visits = visits.filter(patient__user=request.user)

    else:
        visits = Visit.objects.none()

    # ================= FILTERS =================
    if query:
        visits = visits.filter(
            Q(doctor__name__icontains=query) |
            Q(patient__name__icontains=query)
        )

    if main_clinic_id:
        visits = visits.filter(main_clinic_id=main_clinic_id)

    if sub_clinic_id:
        visits = visits.filter(sub_clinic_id=sub_clinic_id)

    visits = visits.order_by('-date')

    paginator = Paginator(visits, 10)
    page_number = request.GET.get('page')
    visits = paginator.get_page(page_number)

    return render(request, 'clinics/visit_list.html', {
        'visits': visits,
        'query': query,
        'main_clinics': MainClinic.objects.all(),
        'sub_clinics': SubClinic.objects.all(),
        'selected_main': main_clinic_id,
        'selected_sub': sub_clinic_id,
    })

@login_required
@user_passes_test(can_manage_visits)
def visit_create_view(request):

    form = VisitForm(request.POST or None, request.FILES or None)

    # ================= المرضى حسب الصلاحية =================
    if request.user.is_superuser or request.user.groups.filter(name='Admin').exists():

        form.fields['patient'].queryset = Patient.objects.all()

    elif is_patient(request.user):

        form.fields['patient'].queryset = Patient.objects.filter(user=request.user)

    elif is_doctor(request.user) or request.user.groups.filter(name='Nurse').exists():

        form.fields['patient'].queryset = Patient.objects.filter(created_by=request.user)

    else:

        form.fields['patient'].queryset = Patient.objects.none()

    # ================= الأطباء =================
    sub_clinic_id = request.POST.get('sub_clinic') or None

    if sub_clinic_id:
        form.fields['doctor'].queryset = Doctor.objects.filter(
            sub_clinic_id=sub_clinic_id
        )

    else:
        form.fields['doctor'].queryset = Doctor.objects.all()

    # ================= SAVE =================
    if form.is_valid():

        visit = form.save(commit=False)

        visit.employee = request.user

        visit.save()

        files = request.FILES.getlist('files')

        for f in files:
            VisitFile.objects.create(
                visit=visit,
                file=f
            )

        messages.success(request, '✅ تمت إضافة الزيارة')

        return redirect('visit_list')

    return render(request, 'clinics/visit_create.html', {
        'form': form
    })


@login_required
@user_passes_test(can_manage_visits)
def visit_edit_view(request, id):
    visit = get_object_or_404(Visit, id=id)
    form = VisitForm(request.POST or None, request.FILES or None, instance=visit)
    sub_clinic_id = request.POST.get('sub_clinic') or visit.sub_clinic_id
    if sub_clinic_id:
        form.fields['doctor'].queryset = Doctor.objects.filter(sub_clinic_id=sub_clinic_id)
    else:
        form.fields['doctor'].queryset = Doctor.objects.all()

    if form.is_valid():
        form.save()
        messages.success(request, '✅ تم تعديل الزيارة')
        return redirect('visit_list')

    return render(request, 'clinics/visit_create.html', {'form': form, 'is_edit': True})


@login_required
@user_passes_test(can_manage_visits)
def visit_delete_view(request, id):
    visit = get_object_or_404(Visit, id=id)
    visit.delete()
    messages.warning(request, '⚠️ تم حذف الزيارة')
    return redirect('visit_list')

@login_required

def visit_detail_view(request, visit_id):
    visit = get_object_or_404(Visit, id=visit_id)
    return render(request, 'clinics/visit_detail.html', {'visit': visit})

@login_required

def delete_file_view(request, id):
    file = get_object_or_404(VisitFile, id=id)
    visit_id = file.visit.id
    if file.file:
        file.file.delete(save=False)
    file.delete()
    messages.success(request, "✅ تم حذف الملف بنجاح")
    return redirect('visit_detail', visit_id=visit_id)


@login_required

def visit_pdf_view(request, visit_id):
    visit = get_object_or_404(Visit, id=visit_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="visit_{visit_id}.pdf"'
    doc = SimpleDocTemplate(response)
    styles = getSampleStyleSheet()
    content = []
    content.append(Paragraph("Medical Report", styles['Title']))
    content.append(Spacer(1, 15))
    content.append(Paragraph(f"Patient: {visit.patient.name}", styles['Normal']))
    content.append(Paragraph(f"Doctor: {visit.doctor_name}", styles['Normal']))
    content.append(Paragraph(f"Clinic: {visit.main_clinic}", styles['Normal']))
    content.append(Spacer(1, 10))
    if visit.analysis_results:
        content.append(Paragraph(f"Analysis: {visit.analysis_results}", styles['Normal']))
        content.append(Spacer(1, 10))
    if visit.medicines:
        content.append(Paragraph(f"Medicines: {visit.medicines}", styles['Normal']))
        content.append(Spacer(1, 10))
    for img_field in [visit.analysis_image, visit.xray_image, visit.prescription_image]:
        if img_field:
            try:
                img = Image(img_field.path, width=200, height=200)
                content.append(img)
                content.append(Spacer(1, 10))
            except:
                pass
    for file in visit.files.all():
        file_path = file.file.path
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            try:
                img = Image(file_path, width=200, height=200)
                content.append(img)
                content.append(Spacer(1, 10))
            except:
                pass
    doc.build(content)
    return response

# ==================== AJAX ====================
@login_required

def load_sub_clinics(request):
    main_id = request.GET.get('main_id')

    if not main_id:
        return JsonResponse([], safe=False)

    subs = SubClinic.objects.filter(main_clinic_id=main_id)

    return JsonResponse(list(subs.values('id', 'name')), safe=False)

@login_required

def load_doctors(request):

    sub_id = request.GET.get("sub_id")

    if not sub_id:

        return JsonResponse([], safe=False)

    doctors = Doctor.objects.filter(sub_clinic_id=sub_id)

    data = list(doctors.values("id", "name"))

    return JsonResponse(data, safe=False)

@login_required

def load_days(request):
    doctor_id = request.GET.get("doctor_id")

    doctor = Doctor.objects.get(id=doctor_id)

    if not doctor.working_days:
        return JsonResponse([], safe=False)

    days = [d.strip() for d in doctor.working_days.replace("و", ",").split(",")]
    return JsonResponse(days, safe=False)

@login_required

def load_hours(request):
    doctor_id = request.GET.get("doctor_id")

    doctor = Doctor.objects.get(id=doctor_id)

    if not doctor.working_hours:
        return JsonResponse({"start": "", "end": ""})

    try:
        start, end = doctor.working_hours.split("-")
    except:
        start, end = "", ""

    return JsonResponse({
        "start": start.strip(),
        "end": end.strip()
    })

# ==================== API ====================

# --- Login API ---
@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})
    return Response({'error': 'Invalid credentials'})

# --- Pagination for Patients ---
class PatientPagination(PageNumberPagination):
    page_size = 5

# --- Patients API ---
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def api_patients(request):
    query = request.GET.get('q', '')
    patients = Patient.objects.all()
    if query:
        patients = patients.filter(Q(name__icontains=query) | Q(phone__icontains=query))
    paginator = PatientPagination()
    result_page = paginator.paginate_queryset(patients, request)
    if request.method == 'GET':
        serializer = PatientSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    elif request.method == 'POST':
        serializer = PatientSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

# --- Patient Detail API ---
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([AllowAny])
def api_patient_detail(request, id):
    patient = get_object_or_404(Patient, id=id)
    if request.method == 'GET':
        serializer = PatientSerializer(patient)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = PatientSerializer(patient, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)
    elif request.method == 'DELETE':
        patient.delete()
        return Response({'message': 'Deleted successfully'})

# --- Visits API ---
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def api_visits(request):
    visits = Visit.objects.select_related('patient', 'doctor', 'sub_clinic', 'main_clinic')
    if request.method == 'GET':
        serializer = VisitSerializer(visits, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = VisitSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(employee=request.user if request.user.is_authenticated else None)
            return Response(serializer.data)
        return Response(serializer.errors)

# --- Clinics API ---
@api_view(['GET'])
@permission_classes([AllowAny])
def api_clinics(request):
    clinics = MainClinic.objects.all()
    serializer = MainClinicSerializer(clinics, many=True)
    return Response(serializer.data)

# --- Sub-Clinics API ---
@api_view(['GET'])
@permission_classes([AllowAny])
def api_sub_clinics(request):
    main_id = request.GET.get('main_clinic')
    subs = SubClinic.objects.filter(main_clinic_id=main_id)
    serializer = SubClinicSerializer(subs, many=True)
    return Response(serializer.data)

# --- Dashboard API ---
@api_view(['GET'])
@permission_classes([AllowAny])
def api_dashboard(request):
    visits_count = Visit.objects.count()
    patients_count = Patient.objects.count()
    clinics_count = MainClinic.objects.count()

    doctors = (
        Visit.objects
        .values('doctor__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    clinics_stats = (
        Visit.objects
        .values('main_clinic__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    return Response({
        "visits": visits_count,
        "patients": patients_count,
        "clinics": clinics_count,
        "doctors": doctors,
        "clinics_stats": clinics_stats
    })


# ==================== Pagination ====================
class DoctorPagination(PageNumberPagination):
    page_size = 5

# ==================== API للدكاترة ====================
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def api_doctors(request):
    query = request.GET.get('q', '')
    doctors = Doctor.objects.all()

    if query:
        doctors = doctors.filter(
            Q(name__icontains=query) | Q(sub_clinic__name__icontains=query)
        )

    paginator = DoctorPagination()
    result_page = paginator.paginate_queryset(doctors, request)

    if request.method == 'GET':
        serializer = DoctorSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    elif request.method == 'POST':
        serializer = DoctorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)
@user_passes_test(is_admin)
def api_dashboard_view(request):
        return render(request, 'clinics/api_dashboard.html')