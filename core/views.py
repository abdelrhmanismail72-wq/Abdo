# Standard library imports
import os
import re
import mimetypes

# Django imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Count, Sum, Q

# Local application imports
from .forms import (
    AdminSetPasswordForm,
    LessonForm,
    LoginForm,
    QuestionForm,
    TestForm,
)
from .models import Attempt, Lesson, Profile, Question, Test


# --- Helper Functions ---

def is_admin(user):
    """Helper function to check if a user has admin privileges."""
    if not user.is_authenticated:
        return False
    try:
        # Check custom profile role or Django's built-in staff/superuser flags
        return user.profile.role == 'admin' or user.is_superuser or user.is_staff
    except Profile.DoesNotExist:
        # If profile doesn't exist, rely on staff/superuser status
        return user.is_superuser or user.is_staff


# --- Authentication Views ---

def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if is_admin(user):
                return redirect('admin_choice')
            return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


@login_required
def user_logout(request):
    logout(request)
    return redirect('login')


def student_register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST.get('email', '')
        full_name = request.POST.get('full_name', '').strip()

        if User.objects.filter(username=username).exists():
            messages.error(request, 'اسم المستخدم موجود بالفعل')
            return redirect('student_register')

        # Create user
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=full_name  # Store full name in first_name field
        )
        
        # Create user profile
        Profile.objects.create(user=user, role='student')
        
        messages.success(request, 'تم إنشاء الحساب بنجاح، يمكنك تسجيل الدخول الآن')
        return redirect('login')

    return render(request, 'student_register.html')


@login_required
def after_login_view(request):
    """Redirects user based on their role after login."""
    if is_admin(request.user):
        return render(request, 'choose_page.html')
    return redirect('home')


# --- General User Views ---

@login_required
def home(request):
    if is_admin(request.user):
        lessons = Lesson.objects.all().order_by('-created_at')
    else:
        lessons = Lesson.objects.filter(is_hidden=False).order_by('-created_at')
    return render(request, 'home.html', {'lessons': lessons})


def test_list(request):
    """Display a list of all available tests."""
    if not request.user.is_authenticated:
        messages.warning(request, 'يجب تسجيل الدخول لعرض الاختبارات')
        return redirect('login')
        
    tests = Test.objects.all().select_related('lesson')
    return render(request, 'test_list.html', {'tests': tests})


@login_required
def user_profile(request):
    """عرض الملف الشخصي للمستخدم مع سجل الاختبارات."""
    # الحصول على محاولات الاختبار للمستخدم مع حساب عدد الأسئلة لكل اختبار في استعلام واحد
    attempts = Attempt.objects.filter(
        user=request.user, completed=True
    ).select_related(
        'test__lesson'
    ).order_by('-completed_at')

    # حساب النسبة المئوية لكل محاولة بشكل منفصل لضمان التحديث
    for attempt in attempts:
        total_questions = attempt.test.question_set.count()
        if total_questions > 0:
            attempt.score_percentage = round((attempt.score / total_questions) * 100)
        else:
            attempt.score_percentage = 0

    # حساب عدد الدروس المكتملة وأعلى النتائج
    completed_lessons = set()
    highest_scores = {}

    for attempt in attempts:
        if attempt.test and attempt.test.lesson:
            lesson_id = attempt.test.lesson.id
            completed_lessons.add(lesson_id)

            # تخزين أعلى نتيجة لكل اختبار
            if lesson_id not in highest_scores or attempt.score_percentage > highest_scores[lesson_id]:
                highest_scores[lesson_id] = attempt.score_percentage
    
    # حساب المتوسط الحسابي لأعلى النتائج
    average_score = 0
    if highest_scores:
        average_score = round(sum(highest_scores.values()) / len(highest_scores))

    # حساب إجمالي وقت الدراسة بالدقائق
    total_study_minutes = 0
    completed_attempts = attempts.filter(completed=True)
    for attempt in completed_attempts:
        if attempt.test:
            time_limit = attempt.test.time_limit
            time_unit = attempt.test.time_unit
            if time_unit == 'seconds':
                total_study_minutes += time_limit / 60
            elif time_unit == 'hours':
                total_study_minutes += time_limit * 60
            else:  # minutes
                total_study_minutes += time_limit

    # تحويل إجمالي الدقائق إلى ساعات ودقائق
    study_hours = int(total_study_minutes // 60)
    study_minutes = int(total_study_minutes % 60)
    study_time_formatted = f"{study_hours}h {study_minutes}m"

    context = {
        'user': request.user,
        'attempts': attempts[:5],  # عرض آخر 5 محاولات فقط
        'completed_lessons_count': len(completed_lessons),
        'average_score': average_score,
        'study_time': study_time_formatted,
        'total_attempts': attempts.count(),
    }
    
    return render(request, 'profile.html', context)


@login_required
def profile_update(request):
    """تحديث بيانات الملف الشخصي للمستخدم."""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if request.method == 'POST':
        user = request.user
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        current_password = request.POST.get('current_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        
        # التحقق من صحة البريد الإلكتروني
        if not email:
            if is_ajax:
                return JsonResponse({'success': False, 'message': 'البريد الإلكتروني مطلوب'})
            messages.error(request, 'البريد الإلكتروني مطلوب')
            return redirect('profile')
            
        # التحقق من عدم استخدام البريد الإلكتروني من قبل مستخدم آخر
        if User.objects.filter(email=email).exclude(pk=user.pk).exists():
            if is_ajax:
                return JsonResponse({'success': False, 'message': 'البريد الإلكتروني مستخدم بالفعل'})
            messages.error(request, 'البريد الإلكتروني مستخدم بالفعل')
            return redirect('profile')
        
        # التحقق من كلمة المرور الحالية إذا تم تقديم كلمة مرور جديدة
        if new_password:
            if not current_password:
                if is_ajax:
                    return JsonResponse({'success': False, 'message': 'يجب إدخال كلمة المرور الحالية لتغيير كلمة المرور'})
                messages.error(request, 'يجب إدخال كلمة المرور الحالية لتغيير كلمة المرور')
                return redirect('profile')
                
            if not user.check_password(current_password):
                if is_ajax:
                    return JsonResponse({'success': False, 'message': 'كلمة المرور الحالية غير صحيحة'})
                messages.error(request, 'كلمة المرور الحالية غير صحيحة')
                return redirect('profile')
            
            # تحديث كلمة المرور إذا تم تقديم كلمة مرور جديدة
            user.set_password(new_password)
            update_session_auth_hash(request, user)  # تحديث الجلسة لتجنب تسجيل الخروج
        
        # تحديث بيانات المستخدم
        user.first_name = full_name
        user.email = email
        user.save()
        
        success_message = 'تم تحديث الملف الشخصي بنجاح' + (' وكلمة المرور' if new_password else '')
        
        if is_ajax:
            return JsonResponse({
                'success': True, 
                'message': success_message,
                'user': {
                    'full_name': user.get_full_name(),
                    'email': user.email
                }
            })
            
        messages.success(request, success_message)
        return redirect('profile')
    
    if is_ajax:
        return JsonResponse({'success': False, 'message': 'طريقة الطلب غير صالحة'}, status=400)
        
    return redirect('profile')


@login_required
def password_change(request):
    """تغيير كلمة مرور المستخدم."""
    if request.method == 'POST':
        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        user = request.user
        current_password = request.POST.get('current_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        # التحقق من صحة كلمة المرور الحالية
        if not user.check_password(current_password):
            error_msg = 'كلمة المرور الحالية غير صحيحة'
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
            return redirect('profile')
        
        # التحقق من تطابق كلمتي المرور الجديدتين
        if new_password1 != new_password2:
            error_msg = 'كلمتا المرور غير متطابقتين'
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
            return redirect('profile')
        
        # التحقق من الحد الأدنى لطول كلمة المرور (4 أحرف أو أرقام أو أي شيء)
        if len(new_password1) < 4:
            error_msg = 'يجب أن تحتوي كلمة المرور على 4 أحرف أو أرقام على الأقل'
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
            return redirect('profile')
        
        # لا توجد قيود أخرى على تعقيد كلمة المرور
        
        try:
            # تغيير كلمة المرور
            user.set_password(new_password1)
            user.save()
            
            # تحديث الجلسة لتجنب تسجيل الخروج
            update_session_auth_hash(request, user)
            
            success_msg = 'تم تغيير كلمة المرور بنجاح'
            if is_ajax:
                return JsonResponse({'success': True, 'message': success_msg})
            messages.success(request, success_msg)
            return redirect('profile')
            
        except Exception as e:
            error_msg = 'حدث خطأ أثناء محاولة تغيير كلمة المرور'
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
            return redirect('profile')
    
    return JsonResponse({'success': False, 'message': 'طلب غير صالح'})


@login_required
def lesson_detail(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    # منع الطلاب من الوصول إلى الدروس المخفية
    if lesson.is_hidden and not is_admin(request.user):
        messages.error(request, "هذا الدرس غير متاح حاليًا.")
        return redirect('home')
    
    test = Test.objects.filter(lesson=lesson).first()
    return render(request, 'lesson_detail.html', {'lesson': lesson, 'test': test})


@login_required
def take_test(request, test_id):
    test = get_object_or_404(Test, pk=test_id)
    attempt, created = Attempt.objects.get_or_create(user=request.user, test=test)
    if attempt.completed:
        return render(request, 'test_result.html', {'attempt': attempt})

    questions = Question.objects.filter(test=test)
    if request.method == 'POST':
        score = 0
        answers_dict = {}  # <-- أضف هذا السطر
        for q in questions:
            ans = request.POST.get(str(q.id), '')
            try:
                ans_num = int(ans)
            except Exception:
                ans_num = 0
            answers_dict[str(q.id)] = ans_num  # <-- أضف هذا السطر
            if ans_num == q.correct_answer:
                score += 1
        attempt.score = score
        attempt.completed = True
        attempt.completed_at = timezone.now()
        attempt.answers = answers_dict  # <-- أضف هذا السطر
        # السماح بالمراجعة يكون عكس خيار "منع المراجعة"
        # إذا كان test.prevent_review = True (منع) => attempt.review_enabled = False (غير مسموح)
        # إذا كان test.prevent_review = False (عدم منع) => attempt.review_enabled = True (مسموح)
        attempt.review_enabled = not test.prevent_review
        attempt.save()
        return render(request, 'test_result.html', {'attempt': attempt})

    return render(request, 'take_test.html', {'test': test, 'questions': questions})


@login_required
def review_answers(request, attempt_id):
    attempt = get_object_or_404(Attempt, id=attempt_id, user=request.user)

    # التحقق مما إذا كانت المراجعة مسموحة لهذا الاختبار
    if attempt.test.prevent_review and not attempt.review_enabled:
        return render(request, 'review_not_allowed.html', status=403)

    questions = Question.objects.filter(test=attempt.test)
    student_answers = attempt.answers or {}
    return render(request, 'review_answers.html', {
        'attempt': attempt,
        'questions': questions,
        'student_answers': student_answers,
    })


# --- Admin Views ---

@login_required
def admin_choice(request):
    """Admin choice page: go to dashboard or lessons page."""
    if not is_admin(request.user):
        return redirect('home')
    return render(request, 'admin_choice.html')


@login_required
def admin_dashboard(request):
    if not is_admin(request.user):
        return redirect('home')

    # تحسين الأداء: جلب بيانات تقدم جميع المستخدمين في استعلام واحد
    users_progress = User.objects.filter(is_superuser=False).annotate(
        attempts_count=Count('attempt', filter=Q(attempt__completed=True)),
        total_score=Sum('attempt__score', filter=Q(attempt__completed=True))
    ).order_by('username')

    lessons = Lesson.objects.all().order_by('-created_at')
    context = {
        'users_progress': users_progress,
        'lessons': lessons,
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
def promote_user(request, user_id):
    if not is_admin(request.user):
        return redirect('home')
    target = get_object_or_404(User, id=user_id)
    profile, created = Profile.objects.get_or_create(user=target)
    profile.role = 'admin'
    profile.save()
    messages.success(request, f'تم ترقية {target.username} إلى أدمن')
    return redirect('admin_dashboard')


@login_required
def demote_user(request, user_id):
    if not is_admin(request.user):
        return redirect('home')
    target = get_object_or_404(User, id=user_id)
    profile, created = Profile.objects.get_or_create(user=target)
    profile.role = 'student'
    profile.save()
    messages.success(request, f'تم إلغاء صلاحية الأدمن عن {target.username}')
    return redirect('admin_dashboard')


@login_required
def admin_set_password(request, user_id):
    if not is_admin(request.user):
        return redirect('home')
    target = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = AdminSetPasswordForm(target, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'تم تغيير كلمة السر للمستخدم {target.username}')
            return redirect('admin_dashboard')
    else:
        form = AdminSetPasswordForm(target)
    return render(
        request, 'admin_set_password.html', {'form': form, 'target': target}
    )


@login_required
def lesson_create(request):
    if not is_admin(request.user):
        return redirect('home')
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES)
        add_test = 'add_test' in request.POST
        if form.is_valid():
            lesson = form.save()
            if add_test:
                return redirect('test_create_from_lesson', lesson_id=lesson.id)
            messages.success(request, 'تم إضافة الدرس بنجاح')
            return redirect('admin_dashboard')
    else:
        form = LessonForm()
    return render(request, 'lesson_form.html', {'form': form})


@login_required
def test_create_from_lesson(request, lesson_id):
    if not is_admin(request.user):
        return redirect('home')
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if request.method == 'POST':
        form = TestForm(request.POST)
        if form.is_valid():
            test = form.save(commit=False)
            test.lesson = lesson
            test.save()
            messages.success(request, 'تم إنشاء الاختبار المرتبط بالدرس')
            return redirect('admin_dashboard')
    else:
        form = TestForm()
    return render(request, 'test_form.html', {'form': form, 'lesson': lesson})


@login_required
def test_edit(request, test_id):
    if not is_admin(request.user):
        return redirect('home')
    test = get_object_or_404(Test, id=test_id)
    if request.method == 'POST':
        form = TestForm(request.POST, instance=test)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل الاختبار بنجاح')
            return redirect('admin_dashboard')
    else:
        form = TestForm(instance=test)
    return render(request, 'test_form.html', {'form': form, 'lesson': test.lesson})

@login_required
def question_add(request, test_id):
    if not is_admin(request.user):
        return redirect('home')
    test = get_object_or_404(Test, id=test_id)
    if request.method == 'POST':
        form = QuestionForm(request.POST, request.FILES)  # <-- أضف request.FILES هنا
        if form.is_valid():
            q = form.save(commit=False)
            q.test = test
            q.save()
            messages.success(request, 'تم إضافة السؤال')
            return redirect('admin_dashboard')
    else:
        form = QuestionForm()
    return render(request, 'question_form.html', {'form': form, 'test': test})


# --- Media Serving Views ---

@login_required
def protected_video(request, lesson_id):
    """A simple way to serve a video file, for logged-in users only."""
    lesson = get_object_or_404(Lesson, id=lesson_id)

    # منع الطلاب من الوصول إلى فيديوهات الدروس المخفية
    if lesson.is_hidden and not is_admin(request.user):
        return HttpResponseForbidden("هذا الدرس غير متاح حاليًا.")

    if not lesson.video_file:
        return HttpResponseForbidden("لا يوجد فيديو لهذا الدرس")

    video_path = os.path.join(settings.MEDIA_ROOT, lesson.video_file.name)
    if not os.path.exists(video_path):
        raise Http404("Video file not found.")

    return FileResponse(open(video_path, 'rb'), content_type='video/mp4')


@login_required
def stream_video(request, lesson_id):
    """
    A more robust video streaming view that supports Range requests,
    allowing seeking in the video player.
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)

    # منع الطلاب من الوصول إلى فيديوهات الدروس المخفية
    if lesson.is_hidden and not is_admin(request.user):
        return HttpResponse("هذا الدرس غير متاح حاليًا.", status=403)

    if not lesson.video_file:
        return HttpResponse("لا يوجد فيديو", status=404)

    video_path = os.path.join(settings.MEDIA_ROOT, lesson.video_file.name)
    if not os.path.exists(video_path):
        raise Http404("Video file not found.")

    file_size = os.path.getsize(video_path)
    content_type, _ = mimetypes.guess_type(video_path)
    content_type = content_type or 'application/octet-stream'

    range_header = request.headers.get('Range', '').strip()
    if range_header:
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if range_match:
            start = int(range_match.group(1))
            end = range_match.group(2)
            end = int(end) if end else file_size - 1
            length = end - start + 1

            with open(video_path, 'rb') as f:
                f.seek(start)
                data = f.read(length)

            resp = HttpResponse(data, status=206, content_type=content_type)
            resp['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            resp['Accept-Ranges'] = 'bytes'
            resp['Content-Length'] = str(length)
            return resp

    resp = FileResponse(open(video_path, 'rb'), content_type=content_type)
    resp['Content-Length'] = str(file_size)
    resp['Accept-Ranges'] = 'bytes'
    return resp


def custom_404_view(request, exception=None):
    """عرض مخصص لصفحة الخطأ 404"""
    return render(request, '404.html', status=404)


def custom_500_view(request):
    """عرض مخصص لصفحة الخطأ 500"""
    return render(request, '500.html', status=500)


def custom_password_reset(request):
    """Custom password reset view that asks for username and email."""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(username=username, email=email)
            request.session['reset_user_id'] = user.id
            return redirect('verify_user_reset')
        except User.DoesNotExist:
            messages.error(request, 'لا يوجد حساب بهذه البيانات. يرجى التحقق من اسم المستخدم والبريد الإلكتروني.')
    
    return render(request, 'registration/password_reset_form.html')


def verify_user_for_reset(request):
    """Verify user for password reset."""
    if 'reset_user_id' not in request.session:
        return redirect('password_reset')
    
    user = get_object_or_404(User, id=request.session['reset_user_id'])
    
    if request.method == 'POST':
        # Here you could add additional verification if needed
        return redirect('password_reset_confirm')
    
    return render(request, 'registration/password_reset_verify.html', {'user': user})


def custom_password_reset_confirm(request):
    """Custom password reset confirmation view."""
    if 'reset_user_id' not in request.session:
        return redirect('password_reset')
    
    user = get_object_or_404(User, id=request.session['reset_user_id'])
    
    if request.method == 'POST':
        password1 = request.POST.get('new_password1')
        password2 = request.POST.get('new_password2')
        
        if password1 != password2:
            messages.error(request, 'كلمتا المرور غير متطابقتين')
            return redirect('password_reset_confirm')
            
        if len(password1) < 4:  # Minimum 4 characters
            messages.error(request, 'يجب أن تتكون كلمة المرور من 4 أحرف على الأقل')
            return redirect('password_reset_confirm')
            
        # Set the new password
        user.set_password(password1)
        user.save()
        
        # Clear the session
        if 'reset_user_id' in request.session:
            del request.session['reset_user_id']
            
        messages.success(request, 'تم تغيير كلمة المرور بنجاح. يمكنك الآن تسجيل الدخول بكلمة المرور الجديدة.')
        return redirect('login')
    
    return render(request, 'registration/password_reset_confirm.html')
