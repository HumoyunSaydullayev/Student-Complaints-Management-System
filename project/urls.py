from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from shikoyatlar import views as dv

urlpatterns = [
    # ============================================
    # SYSTEM
    # ============================================
    path('initialize/', dv.initialize_system, name='initialize_system'),
    path('django-admin/', admin.site.urls),
    
    # ============================================
    # AUTH
    # ============================================
    path('', dv.index, name='index'),
    path('login/<str:role>/', dv.login_view, name='login_view'),
    path('register/', dv.register, name='register'),
    path('logout/', dv.logout_view, name='logout'),
    
    # ============================================
    # STUDENT
    # ============================================
    path('student/dashboard/', dv.student_dashboard, name='student_dashboard'),
    path('student/complaints/', dv.my_complaints, name='my_complaints'),
    path('student/complaint/create/', dv.create_complaint, name='create_complaint'),
    
    # ============================================
    # COMPLAINTS - ALL + COAUTHOR
    # ============================================
    path('complaints/all/', dv.all_complaints, name='all_complaints'),
    path('complaint/<uuid:uuid>/join/', dv.join_as_coauthor, name='join_as_coauthor'),
    path('complaint/<uuid:uuid>/leave/', dv.leave_as_coauthor, name='leave_as_coauthor'),
    
    # ============================================
    # ADMIN
    # ============================================
    path('admin/dashboard/', dv.admin_dashboard, name='admin_dashboard'),
    path('admin/students/', dv.admin_students, name='admin_students'),
    path('admin/officials/', dv.admin_officials, name='admin_officials'),
    path('admin/complaints/', dv.admin_complaints, name='admin_complaints'),
    
    # Delete
    path('admin/user/<int:user_id>/<str:user_type>/delete/', dv.delete_user, name='delete_user'),
    path('admin/complaint/<uuid:uuid>/delete/', dv.delete_complaint_admin, name='delete_complaint_admin'),
    
    # Edit
    path('admin/user/<int:user_id>/<str:user_type>/edit/', dv.edit_user, name='edit_user'),
    path('admin/user/<int:user_id>/<str:user_type>/update/', dv.update_user, name='update_user'),
    path('admin/complaint/<uuid:uuid>/edit/', dv.edit_complaint_admin, name='edit_complaint_admin'),
    path('admin/complaint/<uuid:uuid>/update/', dv.update_complaint_admin, name='update_complaint_admin'),
    
    # ============================================
    # OFFICIAL
    # ============================================
    path('official/dashboard/', dv.official_dashboard, name='official_dashboard'),
    path('official/complaints/', dv.official_complaints, name='official_complaints'),
    
    # ============================================
    # COMPLAINT ACTIONS
    # ============================================
    path('complaint/<uuid:uuid>/action/<str:action>/', dv.complaint_action, name='complaint_action'),
    
    # ============================================
    # COMPLAINT DETAIL
    # ============================================
    path('complaint/<uuid:uuid>/', dv.complaint_detail, name='complaint_detail'),
    path('complaint/<uuid:uuid>/comment/', dv.add_comment, name='add_comment'),
    
    # ============================================
    # PASSWORD
    # ============================================
    path('profile/change-password/', dv.change_password, name='change_password'),
    path('profile/update-password/', dv.update_password, name='update_password'),
]

# Media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
