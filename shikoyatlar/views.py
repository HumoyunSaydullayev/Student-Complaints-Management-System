from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from .models import User, Complaint, Category, Comment, Faculty, Department


# ============================================
# LANDING PAGE
# ============================================
def index(request):
    """Asosiy sahifa - login tanlovlari bilan"""
    if request.user.is_authenticated:
        if request.user.role == 'student':
            return redirect('student_dashboard')
        elif request.user.role == 'admin':
            return redirect('admin_dashboard')
        elif request.user.role == 'official':
            return redirect('official_dashboard')
    
    stats = {
        'total': Complaint.objects.count(),
        'open': Complaint.objects.filter(status='open').count(),
        'in_progress': Complaint.objects.filter(status='in_progress').count(),
        'resolved': Complaint.objects.filter(status='resolved').count(),
        'rejected': Complaint.objects.filter(status='rejected').count(),
    }
    
    return render(request, 'home.html', {'stats': stats})


# ============================================
# UNIVERSAL LOGIN
# ============================================
def login_view(request, role):
    """Universal login - student, admin, official"""
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        if role == 'student':
            student_id = request.POST.get('student_id')
            password = request.POST.get('password')
            
            try:
                user = User.objects.get(student_id=student_id, role='student')
                if user.check_password(password):
                    login(request, user)
                    messages.success(request, f'Xush kelibsiz, {user.full_name}!')
                    return redirect('student_dashboard')
                else:
                    messages.error(request, 'Parol noto\'g\'ri!')
            except User.DoesNotExist:
                messages.error(request, 'Bunday student ID topilmadi!')
        
        else:
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user and user.role == role:
                login(request, user)
                messages.success(request, f'Xush kelibsiz, {user.full_name}!')
                return redirect('admin_dashboard' if role == 'admin' else 'official_dashboard')
            else:
                messages.error(request, 'Username yoki parol noto\'g\'ri!')
    
    gradient = {
        'student': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'admin': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        'official': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
    }.get(role, 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)')

    # Birinchi rangni ajratish ( #667eea )
    import re
    match = re.search(r'#(?:[0-9a-fA-F]{3,4}){2}', gradient)
    primary_color = match.group(0) if match else '#667eea'

    context = {
        'role': role,
        'role_display': {
            'student': 'Talaba',
            'admin': 'Administrator',
            'official': 'Masul Shaxs'
        }.get(role, 'Foydalanuvchi'),
        'role_icon': {
            'student': 'fa-user-graduate',
            'admin': 'fa-user-shield',
            'official': 'fa-user-tie'
        }.get(role, 'fa-user'),
        'role_color': gradient,
        'primary_color': primary_color  # Yangi o'zgaruvchi
    }
    
    return render(request, 'login.html', context)


def logout_view(request):
    """Logout"""
    logout(request)
    messages.success(request, 'Tizimdan chiqdingiz')
    return redirect('index')


# ============================================
# REGISTER
# ============================================
def register(request):
    """Talaba ro'yxatdan o'tish"""
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        student_id = request.POST.get('student_id')
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        group_name = request.POST.get('group_name')
        course = request.POST.get('course')
        faculty_id = request.POST.get('faculty')
        
        if password != password2:
            messages.error(request, 'Parollar mos kelmadi!')
            return redirect('register')
        
        if User.objects.filter(student_id=student_id).exists():
            messages.error(request, 'Bu Student ID allaqachon ro\'yxatdan o\'tgan!')
            return redirect('register')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Bu username band!')
            return redirect('register')
        
        faculty = None
        if faculty_id:
            faculty = Faculty.objects.get(id=faculty_id)
        
        user = User.objects.create_user(
            username=username,
            password=password,
            full_name=full_name,
            student_id=student_id,
            role='student',
            group_name=group_name,
            course=int(course) if course else None,
            faculty=faculty
        )
        
        messages.success(request, 'Ro\'yxatdan o\'tdingiz! Endi tizimga kirishingiz mumkin.')
        return redirect('login_view', role='student')
    
    faculties = Faculty.objects.filter(is_active=True)
    return render(request, 'register.html', {'faculties': faculties})


# ============================================
# STUDENT DASHBOARD
# ============================================
@login_required
def student_dashboard(request):
    """Talaba dashboard"""
    if request.user.role != 'student':
        return redirect('index')
    
    my_complaints = Complaint.objects.filter(student=request.user)
    stats = {
        'total': my_complaints.count(),
        'open_count': my_complaints.filter(status='open').count(),
        'in_progress': my_complaints.filter(status='in_progress').count(),
        'resolved': my_complaints.filter(status='resolved').count(),
        'rejected': Complaint.objects.filter(status='rejected').count(),
    }
    
    recent = my_complaints[:5]
    
    return render(request, 'student_dashboard.html', {
        'stats': stats,
        'recent': recent
    })


@login_required
def my_complaints(request):
    """Mening shikoyatlarim"""
    if request.user.role != 'student':
        return redirect('index')
    
    complaints = Complaint.objects.filter(student=request.user)
    return render(request, 'my_complaints.html', {'complaints': complaints})


@login_required
def create_complaint(request):
    """Yangi shikoyat yaratish"""
    if request.user.role != 'student':
        return redirect('index')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        category_id = request.POST.get('category')
        assigned_to_id = request.POST.get('assigned_to')
        priority = request.POST.get('priority', 'medium')
        
        category = Category.objects.get(id=category_id)
        assigned_to = None
        if assigned_to_id:
            assigned_to = User.objects.get(id=assigned_to_id, role='official')
        
        complaint = Complaint.objects.create(
            student=request.user,
            title=title,
            content=content,
            category=category,
            assigned_to=assigned_to,
            priority=priority,
            status='open'
        )
        
        messages.success(request, 'Shikoyat muvaffaqiyatli yuborildi!')
        return redirect('complaint_detail', uuid=complaint.uuid)
    
    categories = Category.objects.filter(is_active=True)
    officials = User.objects.filter(role='official')
    
    return render(request, 'create_complaint.html', {
        'categories': categories,
        'officials': officials
    })


@login_required
def all_complaints(request):
    """Barcha ochiq shikoyatlar - hammuallif bo'lish"""
    if request.user.role != 'student':
        return redirect('index')
    
    complaints = Complaint.objects.filter(
        Q(status='open') | Q(status='in_progress')
    ).exclude(student=request.user).select_related('student', 'category', 'assigned_to')
    
    for complaint in complaints:
        complaint.is_owner = complaint.student == request.user
        complaint.is_coauthor = complaint.co_authors.filter(id=request.user.id).exists()
    
    return render(request, 'all_complaints.html', {'complaints': complaints})


@login_required
def join_as_coauthor(request, uuid):
    """Hammuallif bo'lib qo'shilish"""
    if request.user.role != 'student':
        messages.error(request, 'Faqat talabalar hammuallif bo\'lishi mumkin!')
        return redirect('index')
    
    complaint = get_object_or_404(Complaint, uuid=uuid)
    
    if complaint.student == request.user:
        messages.warning(request, 'Bu sizning o\'z shikoyatingiz!')
        return redirect('complaint_detail', uuid=uuid)
    
    if complaint.co_authors.filter(id=request.user.id).exists():
        messages.warning(request, 'Siz allaqachon hammuallif sifatida qo\'shilgansiz!')
        return redirect('complaint_detail', uuid=uuid)
    
    if request.method == 'POST':
        complaint.co_authors.add(request.user)
        messages.success(request, 'Siz hammuallif sifatida qo\'shildingiz!')
        return redirect('complaint_detail', uuid=uuid)
    
    return redirect('all_complaints')


@login_required
def leave_as_coauthor(request, uuid):
    """Hammuallif ro'yxatidan chiqish"""
    if request.user.role != 'student':
        return redirect('index')
    
    complaint = get_object_or_404(Complaint, uuid=uuid)
    
    if not complaint.co_authors.filter(id=request.user.id).exists():
        messages.warning(request, 'Siz hammuallif emassiz!')
        return redirect('complaint_detail', uuid=uuid)
    
    if request.method == 'POST':
        complaint.co_authors.remove(request.user)
        messages.success(request, 'Siz hammuallif ro\'yxatidan chiqdingiz!')
        return redirect('all_complaints')
    
    return redirect('all_complaints')


# ============================================
# ADMIN DASHBOARD
# ============================================
@login_required
def admin_dashboard(request):
    """Admin dashboard"""
    if request.user.role != 'admin':
        return redirect('index')
    
    total = Complaint.objects.count()
    open_count = Complaint.objects.filter(status='open').count()
    in_progress = Complaint.objects.filter(status='in_progress').count()
    resolved = Complaint.objects.filter(status='resolved').count()
    rejected= Complaint.objects.filter(status='rejected').count()
    
    total_students = User.objects.filter(role='student').count()
    total_officials = User.objects.filter(role='official').count()
    
    recent = Complaint.objects.select_related('student', 'category')[:10]
    
    return render(request, 'admin_dashboard.html', {
        'total': total,
        'open_count': open_count,
        'in_progress': in_progress,
        'resolved': resolved,
        'rejected': rejected,
        'total_students': total_students,
        'total_officials': total_officials,
        'recent': recent
    })


@login_required
def admin_students(request):
    """Talabalar ro'yxati"""
    if request.user.role != 'admin':
        return redirect('index')
    
    students = User.objects.filter(role='student').select_related('faculty').annotate(
        total_complaints=Count('complaints')
    )
    
    return render(request, 'admin_students.html', {'students': students})


@login_required
def admin_officials(request):
    """Masul shaxslar ro'yxati"""
    if request.user.role != 'admin':
        return redirect('index')
    
    officials = User.objects.filter(role='official').select_related('department').annotate(
        total_assigned=Count('assigned_complaints')
    )
    
    return render(request, 'admin_officials.html', {'officials': officials})


@login_required
def admin_complaints(request):
    """Barcha shikoyatlar - admin"""
    if request.user.role != 'admin':
        return redirect('index')
    
    complaints = Complaint.objects.select_related('student', 'category', 'assigned_to')
    return render(request, 'admin_complaints.html', {'complaints': complaints})


# ============================================
# UNIVERSAL DELETE
# ============================================
@login_required
def delete_user(request, user_id, user_type):
    """Foydalanuvchini o'chirish - universal (student/official)"""
    if request.user.role != 'admin':
        messages.error(request, 'Faqat administrator bu amalni bajarishi mumkin!')
        return redirect('index')
    
    user = get_object_or_404(User, id=user_id, role=user_type)
    
    if request.method == 'POST':
        # POST so'rovda haqiqatan o'chirish
        full_name = user.full_name
        user.delete()
        
        # Talaba bo'lsa, uning shikoyatlari ham o'chiriladi (agar cascade bo'lmasa)
        messages.success(request, f'{full_name} muvaffaqiyatli o\'chirildi!')
        
        if user_type == 'student':
            return redirect('admin_students')
        else:
            return redirect('admin_officials')
    
    # GET so'rovda - tasdiqlash sahifasini ko'rsatish
    back_url = 'admin_students' if user_type == 'student' else 'admin_officials'
    
    context = {
        'item': user,
        'item_type': 'user',
        'user_type': user_type,
        'back_url': back_url,
    }
    
    return render(request, 'confirm_delete.html', context)


@login_required
def delete_complaint_admin(request, uuid):
    """Shikoyatni o'chirish - admin"""
    if request.user.role != 'admin':
        return redirect('index')
    
    complaint = get_object_or_404(Complaint, uuid=uuid)
    
    if request.method == 'POST':
        title = complaint.title
        complaint.delete()
        messages.success(request, f'"{title}" o\'chirildi!')
        return redirect('admin_complaints')
    
    context = {
        'item': complaint,
        'item_type': 'complaint',
        'item_name': complaint.title,
        'back_url': 'admin_complaints'
    }
    
    return render(request, 'confirm_delete.html', context)


# ============================================
# UNIVERSAL EDIT USER
# ============================================
@login_required
def edit_user(request, user_id, user_type):
    """Universal edit - student/official"""
    if request.user.role != 'admin':
        return redirect('index')
    
    user = get_object_or_404(User, id=user_id, role=user_type)
    faculties = Faculty.objects.filter(is_active=True)
    departments = Department.objects.filter(is_active=True)
    
    context = {
        'user': user,
        'user_type': user_type,
        'faculties': faculties,
        'departments': departments,
        'back_url': 'admin_students' if user_type == 'student' else 'admin_officials'
    }
    
    return render(request, 'edit_user.html', context)


@login_required
def update_user(request, user_id, user_type):
    """Universal update - student/official"""
    if request.user.role != 'admin':
        return redirect('index')
    
    user = get_object_or_404(User, id=user_id, role=user_type)
    
    if request.method == 'POST':
        user.full_name = request.POST.get('full_name')
        user.username = request.POST.get('username')
        user.phone = request.POST.get('phone', '')
        user.email = request.POST.get('email', '')
        
        if user_type == 'student':
            user.student_id = request.POST.get('student_id')
            user.group_name = request.POST.get('group_name', '')
            course = request.POST.get('course')
            user.course = int(course) if course else None
            
            faculty_id = request.POST.get('faculty')
            if faculty_id:
                user.faculty = Faculty.objects.get(id=faculty_id)
        
        else:  # official
            user.position = request.POST.get('position', '')
            department_id = request.POST.get('department')
            if department_id:
                user.department = Department.objects.get(id=department_id)
        
        user.save()
        messages.success(request, 'Ma\'lumotlar yangilandi!')
        
        return redirect('admin_students' if user_type == 'student' else 'admin_officials')
    
    return redirect('edit_user', user_id=user_id, user_type=user_type)


@login_required
def edit_complaint_admin(request, uuid):
    """Shikoyatni tahrirlash - admin"""
    if request.user.role != 'admin':
        return redirect('index')
    
    complaint = get_object_or_404(Complaint, uuid=uuid)
    categories = Category.objects.filter(is_active=True)
    officials = User.objects.filter(role='official')
    
    return render(request, 'edit_complaint_admin.html', {
        'complaint': complaint,
        'categories': categories,
        'officials': officials
    })


@login_required
def update_complaint_admin(request, uuid):
    """Shikoyatni yangilash - admin"""
    if request.user.role != 'admin':
        return redirect('index')
    
    complaint = get_object_or_404(Complaint, uuid=uuid)
    
    if request.method == 'POST':
        complaint.title = request.POST.get('title')
        complaint.content = request.POST.get('content')
        
        category_id = request.POST.get('category')
        complaint.category = Category.objects.get(id=category_id)
        
        complaint.priority = request.POST.get('priority')
        complaint.status = request.POST.get('status')
        
        assigned_to_id = request.POST.get('assigned_to')
        if assigned_to_id:
            complaint.assigned_to = User.objects.get(id=assigned_to_id)
        else:
            complaint.assigned_to = None
        
        complaint.save()
        messages.success(request, 'Shikoyat yangilandi!')
        return redirect('admin_complaints')
    
    return redirect('edit_complaint_admin', uuid=uuid)


# ============================================
# OFFICIAL DASHBOARD
# ============================================
@login_required
def official_dashboard(request):
    """Masul shaxs dashboard"""
    if request.user.role != 'official':
        return redirect('index')
    
    my_complaints = Complaint.objects.filter(assigned_to=request.user)
    
    total = my_complaints.count()
    open_count = my_complaints.filter(status='open').count()
    in_progress = my_complaints.filter(status='in_progress').count()
    resolved = my_complaints.filter(status='resolved').count()
    rejected= my_complaints.filter(status='rejected').count()
    
    recent = my_complaints.select_related('student', 'category')[:10]
    
    return render(request, 'official_dashboard.html', {
        'total': total,
        'open_count': open_count,
        'in_progress': in_progress,
        'resolved': resolved,
        'rejected': rejected,
        'recent': recent
    })


@login_required
def official_complaints(request):
    """Menga biriktirilgan shikoyatlar"""
    if request.user.role != 'official':
        return redirect('index')
    
    complaints = Complaint.objects.filter(assigned_to=request.user).select_related('student', 'category')
    return render(request, 'official_complaints.html', {'complaints': complaints})


# ============================================
# UNIVERSAL COMPLAINT ACTION
# ============================================
@login_required
def complaint_action(request, uuid, action):
    """Universal action - accept/resolve/reject"""
    complaint = get_object_or_404(Complaint, uuid=uuid)
    
    # Permission check
    if request.user.role == 'official' and complaint.assigned_to != request.user:
        messages.error(request, 'Bu shikoyat sizga biriktirilmagan!')
        return redirect('complaint_detail', uuid=uuid)
    
    if request.method == 'POST':
        if action == 'accept':
            complaint.status = 'in_progress'
            complaint.save()
            messages.success(request, 'Shikoyat qabul qilindi va ishga olindi!')
            return redirect('complaint_detail', uuid=uuid)
        
        elif action == 'resolve':
            resolution_note = request.POST.get('resolution_note')
            if not resolution_note:
                messages.error(request, 'Javob yozish majburiy!')
                return redirect('complaint_action', uuid=uuid, action=action)
            
            complaint.status = 'resolved'
            complaint.resolution_note = resolution_note
            complaint.resolved_by = request.user
            complaint.resolved_at = timezone.now()
            complaint.save()
            
            messages.success(request, 'Shikoyat hal qilindi!')
            return redirect('complaint_detail', uuid=uuid)
        
        elif action == 'reject':
            rejection_reason = request.POST.get('rejection_reason')
            if not rejection_reason:
                messages.error(request, 'Rad etish sababi majburiy!')
                return redirect('complaint_action', uuid=uuid, action=action)
            
            complaint.status = 'rejected'
            complaint.resolution_note = f"RAD ETILDI: {rejection_reason}"
            complaint.resolved_by = request.user
            complaint.resolved_at = timezone.now()
            complaint.save()
            
            messages.warning(request, 'Shikoyat rad etildi!')
            return redirect('complaint_detail', uuid=uuid)
    
    # Action configuration
    action_config = {
        'accept': {
            'title': 'Shikoyatni Qabul Qilish',
            'icon': 'fa-check',
            'color': '#3b82f6',
            'gradient': 'linear-gradient(135deg, #3b82f6, #2563eb)',
            'button_text': 'Qabul Qilish va Ishga Olish',
            'show_form': False,
            'description': 'Siz bu shikoyat ustida ishlashni boshlaysiz'
        },
        'resolve': {
            'title': 'Shikoyatni Hal Qilish',
            'icon': 'fa-check-circle',
            'color': '#10b981',
            'gradient': 'linear-gradient(135deg, #10b981, #059669)',
            'button_text': 'Hal Qilindi Deb Belgilash',
            'show_form': True,
            'field_name': 'resolution_note',
            'field_label': 'Javob / Yechim',
            'placeholder': 'Shikoyat qanday hal qilindi? Qanday choralar ko\'rildi?',
            'description': 'Ko\'rilgan choralar va natija haqida batafsil yozing'
        },
        'reject': {
            'title': 'Shikoyatni Rad Etish',
            'icon': 'fa-times-circle',
            'color': '#ef4444',
            'gradient': 'linear-gradient(135deg, #ef4444, #dc2626)',
            'button_text': 'Rad Etish',
            'show_form': True,
            'field_name': 'rejection_reason',
            'field_label': 'Rad Etish Sababi',
            'placeholder': 'Nima uchun shikoyat rad etilmoqda? Batafsil tushuntiring...',
            'description': 'Talaba uchun tushunarli sabab yozing'
        }
    }
    
    context = {
        'complaint': complaint,
        'action': action,
        'config': action_config[action]
    }
    
    return render(request, 'complaint_action.html', context)


# ============================================
# COMPLAINT DETAIL
# ============================================
@login_required
def complaint_detail(request, uuid):
    """Shikoyat tafsilotlari"""
    complaint = get_object_or_404(Complaint, uuid=uuid)
    
    # Permission check
    can_view = False
    if request.user.role == 'student':
        can_view = (complaint.student == request.user or 
                   complaint.co_authors.filter(id=request.user.id).exists() or
                   complaint.status in ['open', 'in_progress'])
    elif request.user.role == 'official':
        can_view = complaint.assigned_to == request.user or complaint.status == 'open'
    elif request.user.role == 'admin':
        can_view = True
    
    if not can_view:
        messages.error(request, 'Sizda bu shikoyatni ko\'rish huquqi yo\'q!')
        return redirect('index')
    
    comments = complaint.comments.select_related('user').order_by('created_at')
    coauthors = complaint.co_authors.all()
    
    context = {
        'complaint': complaint,
        'comments': comments,
        'coauthors': coauthors,
        'is_owner': complaint.student == request.user,
        'is_coauthor': complaint.co_authors.filter(id=request.user.id).exists(),
        'can_edit': request.user.role in ['admin', 'official'] and complaint.assigned_to == request.user,
    }
    
    return render(request, 'complaint_detail.html', context)


@login_required
def add_comment(request, uuid):
    """Izoh qo'shish"""
    if request.method == 'POST':
        complaint = get_object_or_404(Complaint, uuid=uuid)
        content = request.POST.get('content')
        
        if content:
            Comment.objects.create(
                complaint=complaint,
                user=request.user,
                content=content
            )
            messages.success(request, 'Izoh qo\'shildi!')
    
    return redirect('complaint_detail', uuid=uuid)


# ============================================
# PAROL O'ZGARTIRISH
# ============================================
@login_required
def change_password(request):
    """Parol o'zgartirish sahifasi"""
    return render(request, 'change_password.html')


@login_required
def update_password(request):
    """Parolni yangilash"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(old_password):
            messages.error(request, 'Eski parol noto\'g\'ri!')
            return redirect('change_password')
        
        if new_password != confirm_password:
            messages.error(request, 'Yangi parollar mos kelmadi!')
            return redirect('change_password')
        
        if len(new_password) < 8:
            messages.error(request, 'Parol kamida 8 belgidan iborat bo\'lishi kerak!')
            return redirect('change_password')
        
        request.user.set_password(new_password)
        request.user.save()
        
        messages.success(request, 'Parol o\'zgartirildi! Qayta kiring.')
        logout(request)
        return redirect('index')
    
    return redirect('change_password')


# ============================================
# SYSTEM INITIALIZATION
# ============================================
def initialize_system(request):
    """Tizimni boshlang'ich ma'lumotlar bilan to'ldirish"""
    from django.contrib.auth.hashers import make_password
    
    # Admin
    if not User.objects.filter(username='admin').exists():
        User.objects.create(
            username='admin',
            password=make_password('admin123'),
            full_name='System Administrator',
            role='admin',
            email='admin@system.uz'
        )
    
    # Fakultetlar
    faculties_data = [
        {'name': 'Axborot Texnologiyalari', 'code': 'IT'},
        {'name': 'Iqtisodiyot', 'code': 'ECON'},
        {'name': 'Muhandislik', 'code': 'ENG'},
    ]
    
    for fac in faculties_data:
        Faculty.objects.get_or_create(name=fac['name'], code=fac['code'])
    
    # Kategoriyalar
    categories_data = [
        {'name': 'Yotoqxona', 'slug': 'yotoqxona', 'icon': 'fa-bed', 'color': '#3b82f6'},
        {'name': 'Ovqatlanish', 'slug': 'ovqatlanish', 'icon': 'fa-utensils', 'color': '#10b981'},
        {'name': 'O\'quv jarayoni', 'slug': 'oquv', 'icon': 'fa-book', 'color': '#f59e0b'},
        {'name': 'Transport', 'slug': 'transport', 'icon': 'fa-bus', 'color': '#8b5cf6'},
        {'name': 'Boshqa', 'slug': 'boshqa', 'icon': 'fa-circle', 'color': '#6b7280'},
    ]
    
    for cat in categories_data:
        Category.objects.get_or_create(
            name=cat['name'],
            defaults={
                'slug': cat['slug'],
                'icon': cat['icon'],
                'color': cat['color']
            }
        )
    
    messages.success(request, 'Tizim initsializatsiya qilindi!')
    return redirect('index')
