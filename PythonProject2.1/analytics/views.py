import csv
import io

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .forms import ResultsUploadForm, TeacherUserLinkForm
from .models import AuditLog, Discipline, Group, Result, Semester, Student, Teacher, TeacherUserLink
from .roles import is_manager, is_teacher


def home(request):
    """Корень сайта: отправляем на панель или на страницу логина."""
    if request.user.is_authenticated:
        return redirect("analytics:dashboard")
    return redirect("login")

def enforce_teacher_scope(request, qs):
    """
    Если пользователь — преподаватель, ограничиваем queryset его Teacher.
    Если преподаватель не привязан — запрещаем доступ (403).
    """
    if is_teacher(request.user) and not is_manager(request.user):
        t = get_linked_teacher(request.user)
        if not t:
            raise PermissionDenied("Профиль преподавателя не привязан к учетной записи.")
        return qs.filter(teacher=t)
    return qs

def get_linked_teacher(user):
    """
    1) Пытаемся найти явную привязку User -> Teacher (TeacherUserLink).
    2) Если нет — fallback на сопоставление по ФИО (для обратной совместимости).
    """
    if not user.is_authenticated:
        return None

    link = TeacherUserLink.objects.select_related("teacher").filter(user=user).first()
    if link:
        return link.teacher

    full_name = user.get_full_name().strip()
    if not full_name:
        return None
    return Teacher.objects.filter(full_name=full_name).first()


@login_required
def dashboard(request):
    """
    Главная панель: фильтры + графики.
    """
    semester_id_raw = request.GET.get('semester')
    discipline_id_raw = request.GET.get('discipline')
    teacher_id_raw = request.GET.get('teacher')

    semester_id = int(semester_id_raw) if semester_id_raw else None
    discipline_id = int(discipline_id_raw) if discipline_id_raw else None
    teacher_id = int(teacher_id_raw) if teacher_id_raw else None

    # Базовый queryset и ограничение для преподавателя
    results_qs = enforce_teacher_scope(request, Result.objects.all())

    # Фильтры панели
    if semester_id:
        results_qs = results_qs.filter(semester_id=semester_id)
    if discipline_id:
        results_qs = results_qs.filter(discipline_id=discipline_id)
    if teacher_id:
        results_qs = results_qs.filter(teacher_id=teacher_id)

    # Если пользователь — преподаватель и не выбирал преподавателя вручную,
    # фиксируем фильтр на его Teacher (чтобы не было «пустого» фильтра в UI).
    limit_to_teacher = False
    current_teacher = None
    if is_teacher(request.user) and not teacher_id:
        current_teacher = get_linked_teacher(request.user)
        if current_teacher:
            teacher_id = current_teacher.id
            limit_to_teacher = True
            results_qs = results_qs.filter(teacher_id=teacher_id)

    # Распределение оценок и «проблемные» группы считаем по уже отфильтрованному qs
    grade_dist = (
        results_qs.values("grade").annotate(cnt=Count("id")).order_by("grade")
    )

    bad_groups = (
        results_qs.values("student__group__id", "student__group__name")
        .annotate(avg_grade=Avg("grade"), results_count=Count("id"))
        .order_by("avg_grade")[:5]
    )

    # средний балл по группам
    groups_stats = (
        Group.objects
        .filter(students__results__in=results_qs)
        .annotate(
            avg_grade=Avg('students__results__grade'),
            results_count=Count('students__results'),
        )
        .order_by('name')
        .distinct()
    )

    # средний балл по дисциплинам
    disciplines_stats = (
        Discipline.objects
        .filter(results__in=results_qs)
        .annotate(
            avg_grade=Avg('results__grade'),
            results_count=Count('results'),
        )
        .order_by('name')
        .distinct()
    )

    # динамика по годам (по полю semester.year)
    year_stats = (
        results_qs
        .values('semester__year')
        .annotate(avg_grade=Avg('grade'), count=Count('id'))
        .order_by('semester__year')
    )

    semesters = Semester.objects.all().order_by('-year', 'term')
    disciplines_all = Discipline.objects.all().order_by('name')
    teachers_all = Teacher.objects.all().order_by('full_name')

    context = {
        'groups_stats': groups_stats,
        'disciplines_stats': disciplines_stats,
        'year_stats': year_stats,
        'grade_dist': grade_dist,
        'bad_groups': bad_groups,
        'semesters': semesters,
        'disciplines_all': disciplines_all,
        'teachers_all': teachers_all,
        'selected_semester_id': semester_id,
        'selected_discipline_id': discipline_id,
        'selected_teacher_id': teacher_id,
        'limit_to_teacher': limit_to_teacher,
        'current_teacher': current_teacher,
        
    }
    return render(request, 'analytics/dashboard.html', context)


@login_required
def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    students = group.students.all()

    students_stats = (
        students
        .annotate(avg_grade=Avg('results__grade'))
        .order_by('-avg_grade')
    )

    context = {
        'group': group,
        'students_stats': students_stats,
    }
    return render(request, 'analytics/group_detail.html', context)


@login_required
def group_profile(request, group_id):
    """
    Профиль группы: детальные графики по студентам и дисциплинам.
    """
    group = get_object_or_404(Group, id=group_id)

    # Средний балл по дисциплинам для группы
    discipline_stats = (
        Discipline.objects
        .filter(results__student__group=group)
        .annotate(
            avg_grade=Avg('results__grade'),
            results_count=Count('results'),
        )
        .order_by('name')
        .distinct()
    )

    # Средний балл по студентам (как в group_detail)
    students_stats = (
        group.students
        .annotate(avg_grade=Avg('results__grade'))
        .order_by('-avg_grade')
    )

    context = {
        'group': group,
        'discipline_stats': discipline_stats,
        'students_stats': students_stats,
    }
    return render(request, 'analytics/group_profile.html', context)


@login_required
def discipline_detail(request, discipline_id):
    """
    Страница дисциплины: средний балл по группам и студентам.
    """
    discipline = get_object_or_404(Discipline, id=discipline_id)

    # Средний балл по группам, где есть эта дисциплина
    groups_stats = (
        Group.objects
        .filter(students__results__discipline=discipline)
        .annotate(
            avg_grade=Avg('students__results__grade'),
            results_count=Count('students__results'),
        )
        .order_by('name')
        .distinct()
    )

    # Средний балл по студентам по этой дисциплине
    students_stats = (
        Student.objects
        .filter(results__discipline=discipline)
        .annotate(avg_grade=Avg('results__grade'))
        .order_by('-avg_grade')
    )

    context = {
        'discipline': discipline,
        'groups_stats': groups_stats,
        'students_stats': students_stats,
    }
    return render(request, 'analytics/discipline_detail.html', context)


@login_required
@user_passes_test(is_manager)
def upload_results(request):
    """
    Загрузка CSV-файла с результатами обучения (только для руководителей/админов).
    """
    if request.method == 'POST':
        form = ResultsUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            try:
                decoded_file = file.read().decode('utf-8')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string, delimiter=';')

                for row in reader:
                    group_name = row['group']
                    student_name = row['student']
                    discipline_name = row['discipline']
                    teacher_name = row.get('teacher', '')
                    semester_year = int(row['year'])
                    semester_term = row['term']
                    grade = float(row['grade'])
                    attendance = float(row.get('attendance', 0))

                    group, _ = Group.objects.get_or_create(name=group_name)
                    student, _ = Student.objects.get_or_create(
                        full_name=student_name,
                        group=group,
                    )
                    discipline, _ = Discipline.objects.get_or_create(
                        name=discipline_name
                    )
                    teacher = None
                    if teacher_name:
                        teacher, _ = Teacher.objects.get_or_create(
                            full_name=teacher_name
                        )
                    semester, _ = Semester.objects.get_or_create(
                        year=semester_year,
                        term=semester_term,
                    )

                    Result.objects.create(
                        student=student,
                        discipline=discipline,
                        teacher=teacher,
                        semester=semester,
                        grade=grade,
                        attendance_percent=attendance,
                    )

                messages.success(request, 'Данные успешно загружены.')
                return redirect('analytics:dashboard')

            except Exception as e:
                messages.error(request, f'Ошибка при обработке файла: {e}')
    else:
        form = ResultsUploadForm()

    return render(request, 'analytics/upload_results.html', {'form': form})

@login_required
def api_summary(request):
    """
    Простой JSON-API с агрегированной аналитикой.
    Поддерживает те же фильтры, что и панель.
    """
    semester_id_raw = request.GET.get('semester')
    discipline_id_raw = request.GET.get('discipline')
    teacher_id_raw = request.GET.get('teacher')

    semester_id = int(semester_id_raw) if semester_id_raw else None
    discipline_id = int(discipline_id_raw) if discipline_id_raw else None
    teacher_id = int(teacher_id_raw) if teacher_id_raw else None

    qs = Result.objects.all()
    if semester_id:
        qs = qs.filter(semester_id=semester_id)
    if discipline_id:
        qs = qs.filter(discipline_id=discipline_id)
    if teacher_id:
        qs = qs.filter(teacher_id=teacher_id)

    groups_stats = (
        Group.objects
        .filter(students__results__in=qs)
        .annotate(
            avg_grade=Avg('students__results__grade'),
            results_count=Count('students__results'),
        )
        .order_by('name')
        .distinct()
    )

    year_stats = (
        qs.values('semester__year')
        .annotate(avg_grade=Avg('grade'), count=Count('id'))
        .order_by('semester__year')
    )

    data = {
        'kpi': {
            'avg_grade': qs.aggregate(a=Avg('grade'))['a'] or 0,
            'students': Student.objects.filter(results__in=qs).distinct().count(),
            'groups': Group.objects.filter(students__results__in=qs).distinct().count(),
            'disciplines': Discipline.objects.filter(results__in=qs).distinct().count(),
        },
        'groups': [
            {
                'name': g.name,
                'avg_grade': g.avg_grade or 0,
                'results_count': g.results_count,
            }
            for g in groups_stats
        ],
        'years': [
            {
                'year': row['semester__year'],
                'avg_grade': row['avg_grade'],
                'count': row['count'],
            }
            for row in year_stats
        ],
    }
    return JsonResponse(data, json_dumps_params={'ensure_ascii': False})


@login_required
@user_passes_test(is_manager)
def export_results(request):
    """
    Экспорт результатов в CSV с учётом текущих фильтров панели.
    """
    semester_id_raw = request.GET.get('semester')
    discipline_id_raw = request.GET.get('discipline')
    teacher_id_raw = request.GET.get('teacher')

    semester_id = int(semester_id_raw) if semester_id_raw else None
    discipline_id = int(discipline_id_raw) if discipline_id_raw else None
    teacher_id = int(teacher_id_raw) if teacher_id_raw else None

    qs = Result.objects.select_related(
        'student', 'student__group',
        'discipline', 'teacher', 'semester'
    )

    if semester_id:
        qs = qs.filter(semester_id=semester_id)
    if discipline_id:
        qs = qs.filter(discipline_id=discipline_id)
    if teacher_id:
        qs = qs.filter(teacher_id=teacher_id)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="results_export.csv"'

    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'group',
        'student',
        'discipline',
        'teacher',
        'year',
        'term',
        'grade',
        'attendance',
    ])

    for r in qs:
        writer.writerow([
            r.student.group.name if r.student and r.student.group else '',
            r.student.full_name if r.student else '',
            r.discipline.name if r.discipline else '',
            r.teacher.full_name if r.teacher else '',
            r.semester.year if r.semester else '',
            r.semester.term if r.semester else '',
            r.grade,
            r.attendance_percent,
        ])

    return response


@login_required
@user_passes_test(is_manager)
def export_pdf(request):
    """
    Экспорт агрегированной аналитики в PDF (для отчёта), с кириллицей.
    """
    semester_id_raw = request.GET.get('semester')
    discipline_id_raw = request.GET.get('discipline')
    teacher_id_raw = request.GET.get('teacher')

    semester_id = int(semester_id_raw) if semester_id_raw else None
    discipline_id = int(discipline_id_raw) if discipline_id_raw else None
    teacher_id = int(teacher_id_raw) if teacher_id_raw else None

    results_qs = Result.objects.all()
    if semester_id:
        results_qs = results_qs.filter(semester_id=semester_id)
    if discipline_id:
        results_qs = results_qs.filter(discipline_id=discipline_id)
    if teacher_id:
        results_qs = results_qs.filter(teacher_id=teacher_id)

    groups_stats = (
        Group.objects
        .filter(students__results__in=results_qs)
        .annotate(
            avg_grade=Avg('students__results__grade'),
            results_count=Count('students__results'),
        )
        .order_by('name')
        .distinct()
    )

    disciplines_stats = (
        Discipline.objects
        .filter(results__in=results_qs)
        .annotate(
            avg_grade=Avg('results__grade'),
            results_count=Count('results'),
        )
        .order_by('name')
        .distinct()
    )

    year_stats = (
        results_qs
        .values('semester__year')
        .annotate(avg_grade=Avg('grade'), count=Count('id'))
        .order_by('semester__year')
    )

    # --- Регистрируем кириллический шрифт ---
    font_path = os.path.join(settings.BASE_DIR, 'analytics', 'fonts', 'DejaVuSans.ttf')
    base_font = 'Helvetica'
    try:
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
            base_font = 'DejaVuSans'
    except Exception:
        # если что-то пошло не так со шрифтом – просто используем Helvetica
        base_font = 'Helvetica'

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="analytics_report.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y = height - 40

    # Заголовок
    p.setFont(base_font, 16)
    p.drawString(50, y, "Отчёт по учебной аналитике")
    y -= 30

    p.setFont(base_font, 10)


    p.drawString(50, y, "Динамика среднего балла по годам:")
    y -= 15
    for row in year_stats:
        line = f"Год {row['semester__year']}: средний балл {row['avg_grade']:.2f} (записей: {row['count']})"
        p.drawString(60, y, line)
        y -= 12
        if y < 80:
            p.showPage()
            y = height - 40
            p.setFont(base_font, 10)

    y -= 10
    p.drawString(50, y, "Средний балл по группам:")
    y -= 15
    for g in groups_stats:
        avg = g.avg_grade or 0
        line = f"Группа {g.name}: {avg:.2f} (оценок: {g.results_count})"
        p.drawString(60, y, line)
        y -= 12
        if y < 80:
            p.showPage()
            y = height - 40
            p.setFont(base_font, 10)

    y -= 10
    p.drawString(50, y, "Средний балл по дисциплинам:")
    y -= 15
    for d in disciplines_stats:
        avg = d.avg_grade or 0
        line = f"{d.name}: {avg:.2f} (оценок: {d.results_count})"
        p.drawString(60, y, line)
        y -= 12
        if y < 80:
            p.showPage()
            y = height - 40
            p.setFont(base_font, 10)

    p.showPage()
    p.save()
    return response

from django.core.paginator import Paginator
from django.utils.timezone import localtime
from .models import AuditLog

@login_required
@user_passes_test(is_manager)
def audit_log(request):
    q = (request.GET.get('q') or '').strip()
    action = (request.GET.get('action') or '').strip()

    qs = AuditLog.objects.select_related('user').order_by('-created_at')
    if action:
        qs = qs.filter(action=action)
    if q:
        qs = qs.filter(details__icontains=q) | qs.filter(user__username__icontains=q)

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'actions': AuditLog.ACTION_CHOICES,
        'selected_action': action,
        'q': q,
    }

    @login_required
    @user_passes_test(is_manager)
    def teacher_links(request):
        """
        Страница для руководителя/админа: привязка пользователей к преподавателям.
        """
        if request.method == "POST":
            form = TeacherUserLinkForm(request.POST)
            if form.is_valid():
                link = form.save()
                messages.success(request, f"Привязка сохранена: {link.user} → {link.teacher}")
                return redirect("analytics:teacher_links")
        else:
            form = TeacherUserLinkForm()

        links = TeacherUserLink.objects.select_related("user", "teacher").order_by("user__username")

        return render(request, "analytics/teacher_links.html", {"form": form, "links": links})

    @login_required
    @user_passes_test(is_manager)
    def teacher_link_delete(request, link_id):
        link = get_object_or_404(TeacherUserLink, id=link_id)
        if request.method == "POST":
            messages.success(request, f"Привязка удалена: {link.user} → {link.teacher}")
            link.delete()
            return redirect("analytics:teacher_links")
        return render(request, "analytics/teacher_link_delete.html", {"link": link})

    return render(request, 'analytics/audit_log.html', context)
from django.shortcuts import get_object_or_404

from .models import TeacherUserLink
from .forms import TeacherUserLinkForm
from .roles import is_manager


@login_required
@user_passes_test(is_manager)
def teacher_links(request):
    if request.method == "POST":
        form = TeacherUserLinkForm(request.POST)
        if form.is_valid():
            link = form.save()
            messages.success(request, f"Привязка сохранена: {link.user} → {link.teacher}")
            return redirect("analytics:teacher_links")
    else:
        form = TeacherUserLinkForm()

    links = TeacherUserLink.objects.select_related("user", "teacher").order_by("user__username")
    return render(request, "analytics/teacher_links.html", {"form": form, "links": links})


@login_required
@user_passes_test(is_manager)
def teacher_link_delete(request, link_id):
    link = get_object_or_404(TeacherUserLink, id=link_id)
    if request.method == "POST":
        messages.success(request, f"Привязка удалена: {link.user} → {link.teacher}")
        link.delete()
        return redirect("analytics:teacher_links")
    return render(request, "analytics/teacher_link_delete.html", {"link": link})
