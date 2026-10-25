from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid


# ============================================
# USER MODEL (Talaba, Admin, Masul Shaxs)
# ============================================
class User(AbstractUser):
    """Foydalanuvchi modeli - 3 xil rol"""
    
    ROLE_CHOICES = [
        ('student', 'Talaba'),
        ('admin', 'Administrator'),
        ('official', 'Masul Shaxs'),
    ]
    
    role = models.CharField('Rol', max_length=20, choices=ROLE_CHOICES, default='student')
    full_name = models.CharField('To\'liq ism', max_length=200, blank=True)
    
    # Talaba uchun
    student_id = models.CharField('Talaba ID', max_length=50, unique=True, null=True, blank=True)
    group_name = models.CharField('Guruh', max_length=50, blank=True)
    faculty = models.ForeignKey('Faculty', on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    course = models.IntegerField('Kurs', null=True, blank=True, choices=[(i, f'{i}-kurs') for i in range(1, 6)])
    
    # Masul shaxs uchun
    position = models.CharField('Lavozim', max_length=200, blank=True)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='officials')
    
    # Kontakt
    phone = models.CharField('Telefon', max_length=13, blank=True)
    avatar = models.ImageField('Avatar', upload_to='avatars/', null=True, blank=True)
    
    # Statistika
    complaints_count = models.IntegerField('Shikoyatlar soni', default=0)
    resolved_count = models.IntegerField('Hal qilingan', default=0)
    
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    updated_at = models.DateTimeField('Yangilangan', auto_now=True)
    
    # Django AbstractUser conflicts ni hal qilish
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='shikoyatlar_user_set',
        related_query_name='shikoyatlar_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='shikoyatlar_user_set',
        related_query_name='shikoyatlar_user',
    )
    
    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'
        db_table = 'shikoyatlar_user'
    
    def __str__(self):
        return self.full_name or self.username
    
    @property
    def is_student(self):
        return self.role == 'student'
    
    @property
    def is_admin_role(self):
        return self.role == 'admin'
    
    @property
    def is_official(self):
        return self.role == 'official'


# ============================================
# FAKULTET
# ============================================
class Faculty(models.Model):
    """Fakultetlar"""
    name = models.CharField('Nomi', max_length=200, unique=True)
    code = models.CharField('Kod', max_length=10, unique=True)
    description = models.TextField('Ta\'rif', blank=True)
    is_active = models.BooleanField('Faol', default=True)
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Fakultet'
        verbose_name_plural = 'Fakultetlar'
        db_table = 'shikoyatlar_faculty'
    
    def __str__(self):
        return self.name


# ============================================
# BO'LIM
# ============================================
class Department(models.Model):
    """Bo'limlar"""
    name = models.CharField('Nomi', max_length=200)
    code = models.CharField('Kod', max_length=20, unique=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, null=True, blank=True, related_name='departments')
    description = models.TextField('Ta\'rif', blank=True)
    is_active = models.BooleanField('Faol', default=True)
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Bo\'lim'
        verbose_name_plural = 'Bo\'limlar'
        db_table = 'shikoyatlar_department'
    
    def __str__(self):
        return self.name


# ============================================
# KATEGORIYA
# ============================================
class Category(models.Model):
    """Shikoyat kategoriyalari"""
    name = models.CharField('Nomi', max_length=100, unique=True)
    slug = models.SlugField('Slug', unique=True)
    icon = models.CharField('Ikon', max_length=50, default='fa-circle')
    color = models.CharField('Rang', max_length=7, default='#3b82f6')
    description = models.TextField('Ta\'rif', blank=True)
    is_active = models.BooleanField('Faol', default=True)
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Kategoriya'
        verbose_name_plural = 'Kategoriyalar'
        db_table = 'shikoyatlar_category'
    
    def __str__(self):
        return self.name


# ============================================
# SHIKOYAT (YANGILANGAN - HAMMUALLIF BILAN)
# ============================================
class Complaint(models.Model):
    """Shikoyatlar - hammuallif funksiyasi bilan"""
    
    STATUS_CHOICES = [
        ('open', 'Ochiq'),
        ('in_progress', 'Jarayonda'),
        ('resolved', 'Hal qilindi'),
        ('rejected', 'Rad etildi'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Past'),
        ('medium', 'O\'rta'),
        ('high', 'Yuqori'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Asosiy muallif
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='complaints', 
        limit_choices_to={'role': 'student'}
    )
    
    # YANGI: Hammuallif (Co-authors) - boshqa talabalar
    co_authors = models.ManyToManyField(
        User,
        related_name='coauthored_complaints',
        blank=True,
        limit_choices_to={'role': 'student'},
        verbose_name='Hammuallif talabalar'
    )
    
    title = models.CharField('Sarlavha', max_length=200)
    content = models.TextField('Mazmun')
    
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='complaints')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='complaints')
    
    status = models.CharField('Holat', max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField('Prioritet', max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    is_anonymous = models.BooleanField('Anonim', default=False)
    
    # Masul shaxs (talaba o'zi tanlaydi)
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_complaints',
        limit_choices_to={'role': 'official'}
    )
    
    resolution_note = models.TextField('Javob', blank=True)
    resolved_at = models.DateTimeField('Hal qilingan vaqt', null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_complaints')
    
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    updated_at = models.DateTimeField('Yangilangan', auto_now=True)
    
    class Meta:
        verbose_name = 'Shikoyat'
        verbose_name_plural = 'Shikoyatlar'
        ordering = ['-created_at']
        db_table = 'shikoyatlar_complaint'
    
    def __str__(self):
        return self.title
    
    def get_status_display_color(self):
        colors = {
            'open': 'orange',
            'in_progress': 'blue',
            'resolved': 'green',
            'rejected': 'red'
        }
        return colors.get(self.status, 'gray')
    
    def get_all_authors(self):
        """Asosiy muallif + hammuallif larni qaytaradi"""
        authors = [self.student]
        authors.extend(list(self.co_authors.all()))
        return authors
    
    def is_author_or_coauthor(self, user):
        """User shikoyat muallifi yoki hammuallifi ekanligini tekshiradi"""
        if self.student == user:
            return True
        return self.co_authors.filter(id=user.id).exists()


# ============================================
# IZOH
# ============================================
class Comment(models.Model):
    """Shikoyatlarga izohlar"""
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField('Izoh')
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Izoh'
        verbose_name_plural = 'Izohlar'
        ordering = ['created_at']
        db_table = 'shikoyatlar_comment'
    
    def __str__(self):
        return f"{self.user.username} - {self.content[:50]}"


# ============================================
# FAYL
# ============================================
class Attachment(models.Model):
    """Fayllar"""
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField('Fayl', upload_to='complaints/')
    file_name = models.CharField('Fayl nomi', max_length=255)
    file_size = models.IntegerField('Hajmi')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    created_at = models.DateTimeField('Yuklangan', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Fayl'
        verbose_name_plural = 'Fayllar'
        db_table = 'shikoyatlar_attachment'
    
    def __str__(self):
        return self.file_name