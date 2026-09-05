from rest_framework import serializers
from .models import MainClinic, SubClinic, Visit, Patient, Doctor


# ==================== Patient ====================

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'


class DoctorSerializer(serializers.ModelSerializer):
    main_clinic = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = ['id', 'name', 'sub_clinic', 'main_clinic']

    def get_main_clinic(self, obj):
        return obj.sub_clinic.main_clinic.name if obj.sub_clinic else None


# ==================== Clinics ====================

class MainClinicSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainClinic
        fields = '__all__'


class SubClinicSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubClinic
        fields = '__all__'


# ==================== Visit ====================

class VisitSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    clinic_name = serializers.CharField(source='main_clinic.name', read_only=True)
    sub_clinic_name = serializers.CharField(source='sub_clinic.name', read_only=True)

    class Meta:
        model = Visit
        fields = '__all__'

