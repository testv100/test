import csv
import io
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from .models import Notification
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from .models import ImportBatch, ImportRowError
from .forms import ResultsUploadForm, TeacherUserLinkForm, NewsForm, FeedbackForm
from .models import (
    AuditLog,
    Discipline,
    Group,
    News,
    Result,
    Semester,
    Student,
    Teacher,
    TeacherUserLink,
)
from .roles import is_manager, is_teacher
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.models import Group as AuthGroup

from django.contrib.auth.decorators import login_required
@login_required
def notifications(request):
    items = request.user.notifications.all()
    return render(request, "analytics/notifications.html", {
        "items": items,
        "page_title": "Уведомления",
        "is_manager": is_manager(request.user),
        "is_teacher": is_teacher(request.user),
    })


@login_required
def notification_mark_read(request, notif_id):
    n = get_object_or_404(request.user.notifications, id=notif_id)
    n.is_read = True
    n.save(update_fields=["is_read"])
    return redirect("analytics:notifications")

@login_required
def cabinet(request):
    context = {
        "is_manager": is_manager(request.user),
        "is_teacher": is_teacher(request.user),
    }
    return render(request, "analytics/cabinet.html", context)
def news_detail(request, pk):
    n = get_object_or_404(News, pk=pk, is_published=True)
    return render(request, "analytics/news_detail.html", {"n": n})


@login_required
@user_passes_test(is_manager)
def news_admin_list(request):
    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "").strip()

    qs = News.objects.all().order_by("-created_at")

    if status == "published":
        qs = qs.filter(is_published=True)
    elif status == "hidden":
        qs = qs.filter(is_published=False)

    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(body__icontains=q) | Q(source__icontains=q))

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "analytics/admin/news_list.html", {
        "page_obj": page_obj,
        "q": q,
        "status": status,
    })


@login_required
@user_passes_test(is_manager)
def news_admin_create(request):
    if request.method == "POST":
        form = NewsForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Новость создана.")
            return redirect("analytics:news_admin_list")
    else:
        form = NewsForm(initial={"is_published": True})

    return render(request, "analytics/admin/news_form.html", {
        "form": form,
        "mode": "create",
    })

def feedback(request):
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Спасибо! Сообщение отправлено.")
            return redirect("analytics:feedback")
    else:
        form = FeedbackForm()

    return render(request, "analytics/feedback.html", {
        "form": form,
        "page_title": "Обратная связь",
        "is_manager": is_manager(request.user) if request.user.is_authenticated else False,
        "is_teacher": is_teacher(request.user) if request.user.is_authenticated else False,
    })

@login_required
@user_passes_test(is_manager)
def news_admin_edit(request, pk):
    n = get_object_or_404(News, pk=pk)

    if request.method == "POST":
        form = NewsForm(request.POST, instance=n)
        if form.is_valid():
            form.save()
            messages.success(request, "Изменения сохранены.")
            return redirect("analytics:news_admin_list")
    else:
        form = NewsForm(instance=n)

    return render(request, "analytics/admin/news_form.html", {
        "form": form,
        "mode": "edit",
        "news": n,
    })
@login_required
@user_passes_test(is_manager)
def import_batches(request):
    batches = ImportBatch.objects.all()
    return render(request, "analytics/admin/import_batches.html", {
        "batches": batches,
        "page_title": "История импортов",
    })


@login_required
@user_passes_test(is_manager)
def import_batch_detail(request, batch_id):
    batch = get_object_or_404(ImportBatch, id=batch_id)
    return render(request, "analytics/admin/import_batch_detail.html", {
        "batch": batch,
        "page_title": "Детали импорта",
    })


@login_required
@user_passes_test(is_manager)
def news_admin_delete(request, pk):
    n = get_object_or_404(News, pk=pk)

    if request.method == "POST":
        n.delete()
        messages.success(request, "Новость удалена.")
        return redirect("analytics:news_admin_list")

    return render(request, "analytics/admin/news_confirm_delete.html", {"news": n})


@login_required
@user_passes_test(is_manager)
def news_admin_toggle_publish(request, pk):
    n = get_object_or_404(News, pk=pk)
    n.is_published = not n.is_published
    n.save(update_fields=["is_published"])
    messages.success(
        request,
        "Новость опубликована." if n.is_published else "Новость скрыта."
    )
    return redirect("analytics:news_admin_list")


def home(request):
    news = News.objects.filter(is_published=True).order_by("-created_at")[:10]

    total_students = Student.objects.count()
    total_groups = Group.objects.count()

    kpi = Result.objects.aggregate(
        avg_grade=Avg("grade"),
        avg_attendance=Avg("attendance_percent"),
        results_count=Count("id"),
    )

    context = {
        "news": news,
        "total_students": total_students,
        "total_groups": total_groups,
        "avg_grade": kpi["avg_grade"] or 0,
        "avg_attendance": kpi["avg_attendance"] or 0,
        "results_count": kpi["results_count"] or 0,
        "is_manager": is_manager(request.user) if request.user.is_authenticated else False,
        "is_teacher": is_teacher(request.user) if request.user.is_authenticated else False,
    }
    return render(request, "analytics/home.html", context)


@login_required
def coming_soon(request):
    return render(request, "analytics/coming_soon.html")


def get_linked_teacher(user):
    if not user.is_authenticated:
        return None

    link = TeacherUserLink.objects.select_related("teacher").filter(user=user).first()
    if link:
        return link.teacher

    full_name = (user.get_full_name() or "").strip()
    if not full_name:
        return None
    return Teacher.objects.filter(full_name=full_name).first()


def enforce_teacher_scope(request, qs):
    if is_teacher(request.user) and not is_manager(request.user):
        t = get_linked_teacher(request.user)
        if not t:
            raise PermissionDenied("Профиль преподавателя не привязан к учетной записи.")
        return qs.filter(teacher=t)
    return qs


@login_required
def dashboard(request):
    semester_id = request.GET.get("semester")
    discipline_id = request.GET.get("discipline")
    teacher_id = request.GET.get("teacher")

    results_qs = enforce_teacher_scope(
        request,
        Result.objects.select_related("student", "student__group", "discipline", "teacher", "semester")
    )

    if semester_id:
        results_qs = results_qs.filter(semester_id=int(semester_id))
    if discipline_id:
        results_qs = results_qs.filter(discipline_id=int(discipline_id))
    if teacher_id and is_manager(request.user):
        results_qs = results_qs.filter(teacher_id=int(teacher_id))

    # ИСПРАВЛЕНО: students__results вместо student__results
    groups_stats = (
        Group.objects
        .filter(students__results__in=results_qs)
        .annotate(
            avg_grade=Avg("students__results__grade"),
            results_count=Count("students__results"),
        )
        .order_by("name")
        .distinct()
    )

    disciplines_stats = (
        Discipline.objects
        .filter(results__in=results_qs)
        .annotate(
            avg_grade=Avg("results__grade"),
            results_count=Count("results"),
        )
        .order_by("name")
        .distinct()
    )

    year_stats = (
        results_qs
        .values("semester__year")
        .annotate(avg_grade=Avg("grade"), count=Count("id"))
        .order_by("semester__year")
    )

    semesters = Semester.objects.all().order_by("-year", "term")
    disciplines_all = Discipline.objects.all().order_by("name")
    teachers_all = Teacher.objects.all().order_by("full_name")

    context = {
        "groups_stats": groups_stats,
        "disciplines_stats": disciplines_stats,
        "year_stats": year_stats,
        "semesters": semesters,
        "disciplines_all": disciplines_all,
        "teachers_all": teachers_all,
        "selected_semester_id": int(semester_id) if semester_id else None,
        "selected_discipline_id": int(discipline_id) if discipline_id else None,
        "selected_teacher_id": int(teacher_id) if teacher_id else None,
        "is_manager": is_manager(request.user),
        "is_teacher": is_teacher(request.user),
    }
    return render(request, "analytics/dashboard.html", context)


@login_required
def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    students_stats = (
        group.students
        .annotate(avg_grade=Avg("results__grade"))
        .order_by("-avg_grade", "full_name")
    )

    q = (request.GET.get("q") or "").strip()
    if q:
        students_stats = students_stats.filter(full_name__icontains=q)

    paginator = Paginator(students_stats, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "analytics/group_detail.html", {
        "group": group,
        "page_obj": page_obj,
        "q": q,
    })


@login_required
def group_profile(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    discipline_stats = (
        Discipline.objects
        .filter(results__student__group=group)
        .annotate(
            avg_grade=Avg("results__grade"),
            results_count=Count("results"),
        )
        .order_by("name")
        .distinct()
    )

    students_stats = (
        group.students
        .annotate(avg_grade=Avg("results__grade"))
        .order_by("-avg_grade", "full_name")
    )

    return render(request, "analytics/group_profile.html", {
        "group": group,
        "discipline_stats": discipline_stats,
        "students_stats": students_stats,
    })


@login_required
def discipline_detail(request, discipline_id):
    discipline = get_object_or_404(Discipline, id=discipline_id)

    groups_stats = (
        Group.objects
        .filter(students__results__discipline=discipline)
        .annotate(
            avg_grade=Avg("students__results__grade"),
            results_count=Count("students__results"),
        )
        .order_by("name")
        .distinct()
    )

    students_stats = (
        Student.objects
        .filter(results__discipline=discipline)
        .annotate(avg_grade=Avg("results__grade"))
        .order_by("-avg_grade", "full_name")
    )

    return render(request, "analytics/discipline_detail.html", {
        "discipline": discipline,
        "groups_stats": groups_stats,
        "students_stats": students_stats,
    })


@login_required
def api_summary(request):
    semester_id = request.GET.get("semester")
    discipline_id = request.GET.get("discipline")
    teacher_id = request.GET.get("teacher")

    qs = enforce_teacher_scope(request, Result.objects.all())

    if semester_id:
        qs = qs.filter(semester_id=int(semester_id))
    if discipline_id:
        qs = qs.filter(discipline_id=int(discipline_id))
    if teacher_id and is_manager(request.user):
        qs = qs.filter(teacher_id=int(teacher_id))

    data = {
        "kpi": {
            "avg_grade": qs.aggregate(a=Avg("grade"))["a"] or 0,
            "avg_attendance": qs.aggregate(a=Avg("attendance_percent"))["a"] or 0,
            "students": Student.objects.filter(results__in=qs).distinct().count(),
            "groups": Group.objects.filter(students__results__in=qs).distinct().count(),
            "disciplines": Discipline.objects.filter(results__in=qs).distinct().count(),
        }
    }
    return JsonResponse(data, json_dumps_params={"ensure_ascii": False})


@login_required
@user_passes_test(is_manager)
def upload_results(request):
    if request.method == "POST":
        form = ResultsUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data["file"]
            try:
                decoded_file = file.read().decode("utf-8")
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string, delimiter=";")
                batch = ImportBatch.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    file_name=getattr(file, "name", "upload.csv"),
                )
                total = created = updated = errors = 0

                for idx, row in enumerate(reader, start=1):
                    total += 1
                    try:
                        group_name = row["group"]
                        student_name = row["student"]
                        discipline_name = row["discipline"]
                        teacher_name = row.get("teacher", "")
                        semester_year = int(row["year"])
                        semester_term = row["term"]
                        grade = float(row["grade"])
                        attendance = float(row.get("attendance", 0) or 0)

                        group, _ = Group.objects.get_or_create(name=group_name)
                        student, _ = Student.objects.get_or_create(full_name=student_name, group=group)
                        discipline, _ = Discipline.objects.get_or_create(name=discipline_name)

                        teacher = None
                        if teacher_name:
                            teacher, _ = Teacher.objects.get_or_create(full_name=teacher_name)

                        semester, _ = Semester.objects.get_or_create(year=semester_year, term=semester_term)

                        # вместо Result.objects.create — делаем update_or_create, чтобы не плодить дубли
                        obj, was_created = Result.objects.update_or_create(
                            student=student,
                            discipline=discipline,
                            teacher=teacher,
                            semester=semester,
                            defaults={"grade": grade, "attendance_percent": attendance},
                        )
                        if was_created:
                            created += 1
                        else:
                            updated += 1

                    except Exception as e:
                        errors += 1
                        ImportRowError.objects.create(
                            batch=batch,
                            row_number=idx,
                            raw_row=str(row),
                            error=str(e),
                        )
                batch.total_rows = total
                batch.created_results = created
                batch.updated_results = updated
                batch.error_rows = errors
                batch.save(update_fields=["total_rows", "created_results", "updated_results", "error_rows"])
                messages.success(request, "Данные успешно загружены.")
                return redirect("analytics:dashboard")

            except Exception as e:
                messages.error(request, f"Ошибка при обработке файла: {e}")
    else:
        form = ResultsUploadForm()

    return render(request, "analytics/upload_results.html", {"form": form})

@login_required
@user_passes_test(is_manager)
def import_batches(request):
    batches = ImportBatch.objects.all()
    return render(request, "analytics/admin/import_batches.html", {"batches": batches})

@login_required
@user_passes_test(is_manager)
def import_batch_detail(request, batch_id):
    batch = get_object_or_404(ImportBatch, id=batch_id)
    return render(request, "analytics/admin/import_batch_detail.html", {"batch": batch})
@login_required
def notifications(request):
    qs = request.user.notifications.all()
    return render(request, "analytics/notifications.html", {"items": qs})

@login_required
def notification_mark_read(request, notif_id):
    n = get_object_or_404(request.user.notifications, id=notif_id)
    n.is_read = True
    n.save(update_fields=["is_read"])
    return redirect("analytics:notifications")

@login_required
@user_passes_test(is_manager)
def audit_log(request):
    q = (request.GET.get("q") or "").strip()
    action = (request.GET.get("action") or "").strip()

    qs = AuditLog.objects.select_related("user").order_by("-created_at", "-id")
    if action:
        qs = qs.filter(action=action)
    if q:
        qs = qs.filter(details__icontains=q) | qs.filter(user__username__icontains=q)

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "analytics/audit_log.html", {
        "page_obj": page_obj,
        "actions": AuditLog.ACTION_CHOICES,
        "selected_action": action,
        "q": q,
    })


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


@login_required
def export_results(request):
    semester_id = request.GET.get("semester")
    discipline_id = request.GET.get("discipline")
    teacher_id = request.GET.get("teacher")

    qs = enforce_teacher_scope(
        request,
        Result.objects.select_related("student", "student__group", "discipline", "teacher", "semester")
    )

    if semester_id:
        qs = qs.filter(semester_id=int(semester_id))
    if discipline_id:
        qs = qs.filter(discipline_id=int(discipline_id))
    if teacher_id and is_manager(request.user):
        qs = qs.filter(teacher_id=int(teacher_id))

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="results_export.csv"'

    writer = csv.writer(response, delimiter=";")
    writer.writerow(["group", "student", "discipline", "teacher", "year", "term", "grade", "attendance"])

    for r in qs:
        writer.writerow([
            r.student.group.name if r.student and r.student.group else "",
            r.student.full_name if r.student else "",
            r.discipline.name if r.discipline else "",
            r.teacher.full_name if r.teacher else "",
            r.semester.year if r.semester else "",
            r.semester.term if r.semester else "",
            r.grade,
            r.attendance_percent,
        ])

    return response


@login_required
def export_pdf(request):
    semester_id = request.GET.get("semester")
    discipline_id = request.GET.get("discipline")
    teacher_id = request.GET.get("teacher")

    results_qs = enforce_teacher_scope(request, Result.objects.all())

    if semester_id:
        results_qs = results_qs.filter(semester_id=int(semester_id))
    if discipline_id:
        results_qs = results_qs.filter(discipline_id=int(discipline_id))
    if teacher_id and is_manager(request.user):
        results_qs = results_qs.filter(teacher_id=int(teacher_id))

    groups_stats = (
        Group.objects
        .filter(students__results__in=results_qs)
        .annotate(avg_grade=Avg("students__results__grade"), results_count=Count("students__results"))
        .order_by("name")
        .distinct()
    )

    disciplines_stats = (
        Discipline.objects
        .filter(results__in=results_qs)
        .annotate(avg_grade=Avg("results__grade"), results_count=Count("results"))
        .order_by("name")
        .distinct()
    )

    year_stats = (
        results_qs.values("semester__year")
        .annotate(avg_grade=Avg("grade"), count=Count("id"))
        .order_by("semester__year")
    )

    font_path = os.path.join(settings.BASE_DIR, "analytics", "fonts", "DejaVuSans.ttf")
    base_font = "Helvetica"
    try:
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
            base_font = "DejaVuSans"
    except Exception:
        base_font = "Helvetica"

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="analytics_report.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y = height - 40

    p.setFont(base_font, 16)
    p.drawString(50, y, "Отчёт по учебной аналитике")
    y -= 30

    p.setFont(base_font, 10)

    p.drawString(50, y, "Динамика среднего балла по годам:")
    y -= 15
    for row in year_stats:
        p.drawString(60, y, f"Год {row['semester__year']}: средний балл {row['avg_grade']:.2f} (записей: {row['count']})")
        y -= 12
        if y < 80:
            p.showPage()
            y = height - 40
            p.setFont(base_font, 10)

    y -= 10
    p.drawString(50, y, "Средний балл по группам:")
    y -= 15
    for g in groups_stats:
        p.drawString(60, y, f"Группа {g.name}: {(g.avg_grade or 0):.2f} (оценок: {g.results_count})")
        y -= 12
        if y < 80:
            p.showPage()
            y = height - 40
            p.setFont(base_font, 10)

    y -= 10
    p.drawString(50, y, "Средний балл по дисциплинам:")
    y -= 15
    for d in disciplines_stats:
        p.drawString(60, y, f"{d.name}: {(d.avg_grade or 0):.2f} (оценок: {d.results_count})")
        y -= 12
        if y < 80:
            p.showPage()
            y = height - 40
            p.setFont(base_font, 10)

    p.showPage()
    p.save()
    return response


def info(request, slug):
    pages = {
        "about": {
            "title": "Сведения",
            "template": "analytics/info/about.html",
        },
        "applicant": {
            "title": "Абитуриенту",
            "template": "analytics/info/applicant.html",
        },
        "student": {
            "title": "Студенту",
            "template": "analytics/info/student.html",
        },
        "distance": {
            "title": "Дистанционное",
            "template": "analytics/info/distance.html",
        },
        "sitemap": {
            "title": "Карта сайта",
            "template": "analytics/info/sitemap.html",
        },
        "search": {
            "title": "Поиск",
            "template": "analytics/info/search.html",
        },
        "privacy": {
            "title": "Политика обработки персональных данных",
            "template": "analytics/info/privacy.html",
        },
    }

    page = pages.get(slug)
    if not page:
        raise Http404("Страница не найдена")

    return render(
        request,
        page["template"],
        {"page_title": page["title"], "slug": slug},
    )


    template = templates.get(slug)
    if not template:
        raise Http404("Страница не найдена")

    return render(request, template)


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            group, created = AuthGroup.objects.get_or_create(name="student")
            user.groups.add(group)
            login(request, user)
            messages.success(request, "Регистрация прошла успешно!")
            return redirect("analytics:dashboard")
    else:
        form = UserCreationForm()


    return render(request, "registration/register.html", {"form": form})