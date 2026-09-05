from django.core.management.base import BaseCommand
from clinics.models import MainClinic, SubClinic
import pandas as pd

class Command(BaseCommand):
    help = "Import clinics data from Excel file"

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

        if 'المجموعة' not in df.columns or 'اسم العيادة' not in df.columns:
            self.stdout.write(self.style.ERROR("❌ الأعمدة لازم تكون: 'المجموعة' و 'اسم العيادة'"))
            return

        count = 0

        for _, row in df.iterrows():
            main_name = str(row.get('المجموعة', '')).strip()
            sub_name = str(row.get('اسم العيادة', '')).strip()

            if not main_name or not sub_name:
                continue

            main_clinic, _ = MainClinic.objects.get_or_create(name=main_name)

            SubClinic.objects.get_or_create(
                main_clinic=main_clinic,
                name=sub_name
            )

            count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ تم استيراد {count} عيادة بنجاح"))