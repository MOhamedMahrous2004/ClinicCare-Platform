from django.core.management.base import BaseCommand
from clinics.models import SubClinic, Doctor
import pandas as pd


class Command(BaseCommand):
    help = "Import doctors from Excel file"

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str)

    def handle(self, *args, **kwargs):
        excel_file = kwargs['excel_file']

        try:
            df = pd.read_excel(excel_file)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
            return

        print("📊 الأعمدة:", df.columns)


        df.columns = df.columns.str.strip()


        required_columns = ['اسم العيادة', 'اسم الطبيب', 'أيام العمل', 'ساعات العمل']

        for col in required_columns:
            if col not in df.columns:
                self.stdout.write(self.style.ERROR(f"❌ العمود '{col}' مش موجود"))
                return

        count = 0

        for _, row in df.iterrows():
            clinic_name = str(row.get('اسم العيادة', '')).strip()
            doctor_name = str(row.get('اسم الطبيب', '')).strip()
            work_days = str(row.get('أيام العمل', '')).strip()
            work_hours = str(row.get('ساعات العمل', '')).strip()

            if not clinic_name or not doctor_name:
                continue


            try:
                sub_clinic = SubClinic.objects.get(name=clinic_name)
            except SubClinic.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"⚠️ العيادة غير موجودة: {clinic_name}"))
                continue


            Doctor.objects.update_or_create(
                name=doctor_name,
                sub_clinic=sub_clinic,
                defaults={
                    'working_days': work_days,
                    'working_hours': work_hours
                }
            )

            count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ تم استيراد {count} دكتور بنجاح"))