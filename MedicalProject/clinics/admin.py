from django.contrib import admin
from django.utils.html import format_html
from .models import MainClinic, SubClinic, Visit, Patient, VisitFile,Doctor


# -------------------- Main Clinic --------------------
@admin.register(MainClinic)
class MainClinicAdmin(admin.ModelAdmin):
    list_display = ('name',)


# -------------------- Sub Clinic --------------------
@admin.register(SubClinic)
class SubClinicAdmin(admin.ModelAdmin):
    list_display = ('name', 'main_clinic')



@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'sub_clinic', 'working_days', 'working_hours')  # عرض الأيام والساعات
    search_fields = ('name', 'sub_clinic__name')  # البحث حسب الاسم أو العيادة
    list_filter = ('sub_clinic',)

# -------------------- Patient --------------------
@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'age',
        'gender',
        'phone',
        'has_chronic',
        'chronic_diseases'
    )

    list_filter = ('gender', 'has_chronic')
    search_fields = ('name', 'phone')


# -------------------- Visit --------------------

# 👇 Inline لرفع أكتر من ملف
class VisitFileInline(admin.TabularInline):
    model = VisitFile
    extra = 1


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):

    list_display = (
        'patient',
        'main_clinic',
        'sub_clinic',
        'doctor',
        'show_files',
        'date'
    )

    #  نضيف الملفات جوه الزيارة
    inlines = [VisitFileInline]

    readonly_fields = ('show_files',)

    #  عرض كل الملفات (صور + PDF)
    def show_files(self, obj):
        if not obj.files.exists():
            return "لا يوجد"

        html = ""
        for f in obj.files.all():
            if f.file:
                if f.file.url.lower().endswith('.pdf'):
                    html += f'<a href="{f.file.url}" target="_blank">📄 فتح PDF</a><br>'
                else:
                    html += f'<img src="{f.file.url}" width="80" style="margin:5px; border-radius:8px;" /><br>'

        return format_html(html)

    show_files.short_description = "الملفات"
