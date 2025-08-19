from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import after_login_view
from . import views
from .forms import CustomPasswordResetForm

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/promote/<int:user_id>/', views.promote_user, name='promote_user'),
    path('dashboard/demote/<int:user_id>/', views.demote_user, name='demote_user'),
    path('dashboard/set_password/<int:user_id>/', views.admin_set_password, name='admin_set_password'),
    path('dashboard/lesson/create/', views.lesson_create, name='lesson_create'),
    path('dashboard/lesson/<int:lesson_id>/create_test/', views.test_create_from_lesson, name='test_create_from_lesson'),
    path('dashboard/test/<int:test_id>/add_question/', views.question_add, name='question_add'),
    path('dashboard/test/<int:test_id>/edit/', views.test_edit, name='test_edit'),
    # روابط أخرى موجودة عندك سابقًا
    path('', views.home, name='home'),
    path('lesson/<int:pk>/', views.lesson_detail, name='lesson_detail'),
    path('take_test/<int:test_id>/', views.take_test, name='take_test'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/student/', views.student_register, name='student_register'),
    path('media/protected/lesson/<int:lesson_id>/', views.protected_video, name='protected_video'),
    path('media/protected/lesson/<int:lesson_id>/stream/', views.stream_video, name='stream_video'),
    path('after_login/', views.after_login_view, name='after_login'),
    path('admin_choice/', views.admin_choice, name='admin_choice'),  # أضف هذا السطر
    path('review_answers/<int:attempt_id>/', views.review_answers, name='review_answers'),
    path('tests/', views.test_list, name='test_form'),
    path('profile/', views.user_profile, name='profile'),  # إضافة مسار الملف الشخصي
    path('profile/update/', views.profile_update, name='profile_update'),  # تحديث الملف الشخصي
    path('password/change/', views.password_change, name='password_change'),  # تغيير كلمة المرور
    
    # Custom password reset flow
    path('password_reset/', views.custom_password_reset, name='password_reset'),
    path('password_reset/verify/', views.verify_user_for_reset, name='verify_user_reset'),
    path('password_reset/change/', views.custom_password_reset_confirm, name='password_reset_confirm'),
]
