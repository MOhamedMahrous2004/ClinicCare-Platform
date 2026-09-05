from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [

    # -------------------- Auth --------------------
    path('login/', auth_views.LoginView.as_view(template_name='clinics/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register_view, name='register'),
    # -------------------- Home & Dashboard --------------------
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # -------------------- Patients --------------------
    path('patients/', views.patients_list_view, name='patients_list'),
    path('patients/add/', views.patient_create_view, name='patient_create'),
    path('patients/edit/<int:id>/', views.patient_edit_view, name='patient_edit'),
    path('patients/delete/<int:id>/', views.patient_delete_view, name='patient_delete'),

    # -------------------- Doctors --------------------
    path('doctors/', views.doctor_list_view, name='doctor_list'),
    path('doctors/add/', views.doctor_create_view, name='doctor_create'),
    path('doctors/edit/<int:pk>/', views.doctor_edit_view, name='doctor_edit'),
    path('doctors/delete/<int:pk>/', views.doctor_delete_view, name='doctor_delete'),

    # -------------------- Visits --------------------
    path('visits/', views.visit_list_view, name='visit_list'),
    path('visits/add/', views.visit_create_view, name='visit_create'),
    path('visits/<int:visit_id>/', views.visit_detail_view, name='visit_detail'),
    path('visits/pdf/<int:visit_id>/', views.visit_pdf_view, name='visit_pdf'),
    path('visits/edit/<int:id>/', views.visit_edit_view, name='visit_edit'),
    path('visits/delete/<int:id>/', views.visit_delete_view, name='visit_delete'),

    # -------------------- Clinics --------------------
    path('clinics/', views.clinics_list_view, name='clinics_list'),
    path('clinics/add-main/', views.main_clinic_add_view, name='main_clinic_add'),
    path('clinics/add-sub/', views.sub_clinic_add_view, name='sub_clinic_add'),

    path('clinics/edit-main/<int:id>/', views.edit_main_clinic_view, name='edit_main_clinic'),
    path('clinics/delete-main/<int:id>/', views.delete_main_clinic_view, name='delete_main_clinic'),

    path('clinics/edit-sub/<int:id>/', views.edit_sub_clinic_view, name='edit_sub_clinic'),
    path('clinics/delete-sub/<int:id>/', views.delete_sub_clinic_view, name='delete_sub_clinic'),

    # -------------------- Files --------------------
    path('delete-file/<int:id>/', views.delete_file_view, name='delete_file'),

    # -------------------- APIs --------------------
    path('api/login/', views.api_login),
    path('api/patients/', views.api_patients),
    path('api/patients/<int:id>/', views.api_patient_detail),
    path('api/visits/', views.api_visits),
    path('api/clinics/', views.api_clinics),
    path('api/sub-clinics/', views.api_sub_clinics),
    path('api/dashboard/', views.api_dashboard),
    path('api/doctors/', views.api_doctors),
    path('api-dashboard/', views.api_dashboard_view, name='api_dashboard'),

    # -------------------- AJAX (IMPORTANT) --------------------
    path('clinics/load-sub-clinics/', views.load_sub_clinics, name='load_sub_clinics'),
    path('clinics/load-doctors/', views.load_doctors, name='load_doctors'),
    path('clinics/load-days/', views.load_days, name='load_days'),
    path('clinics/load-hours/', views.load_hours, name='load_hours'),
    path('load-doctors/', views.load_doctors),

    # -------------------- Appointment Create --------------------
    path('create/', views.create_appointment, name='create_appointment'),
    path('appointments/', views.appointments_list_view, name='appointments_list'),
path('appointments/<int:id>/edit/', views.edit_appointment, name='edit_appointment'),
path('appointments/<int:id>/delete/', views.delete_appointment, name='delete_appointment'),
    path('clinics/doctor-available-days/', views.doctor_available_days, name='doctor_available_days'),
]