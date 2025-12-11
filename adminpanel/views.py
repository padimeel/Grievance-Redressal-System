# adminpanel/views.py
import csv
import logging
from django.http import StreamingHttpResponse, JsonResponse
from django.utils.encoding import smart_str
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test, login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, F
from django.utils.dateparse import parse_date
from django.contrib import messages
from django import forms
from rest_framework import status, serializers as drf_serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model

# local imports (models + serializers)
from adminpanel.models import Category, Grievance, GrievanceRemark, ChangeLog, Department
from .serializers import (
    CategorySerializer,
    GrievanceListSerializer,
    GrievanceDetailSerializer,
    GrievanceCreateUpdateSerializer,
    GrievanceRemarkSerializer,
)
from accounts.permissions import IsAdminPanel

logger = logging.getLogger(__name__)
User = get_user_model()


# -----------------------
# Helpers
# -----------------------
def is_admin_user(user):
    """True for staff/superuser or user.role == 'admin'."""
    return user.is_authenticated and (
        getattr(user, "is_staff", False)
        or getattr(user, "is_superuser", False)
        or getattr(user, "role", None) == "admin"
    )


def normalize_department(data, auto_create=True):
    """
    Convert incoming data so that if the client sent 'department' as a name (string),
    we map it to 'department_id' (pk) which the serializers expect.

    If auto_create=True (default) we will create the Department when the name
    does not exist. If auto_create=False we raise a DRF ValidationError.
    """
    # if frontend already sent department_id, do nothing
    if "department_id" in data:
        return data

    # if they provided department as an object/string, try to resolve by id or name
    if "department" in data and data.get("department") not in (None, ""):
        dept_val = data.get("department")
        # try treat as id first
        try:
            dept_id = int(dept_val)
            data["department_id"] = dept_id
            return data
        except (ValueError, TypeError):
            # treat as name (case-insensitive)
            dept_name = str(dept_val).strip()
            try:
                dept = Department.objects.get(name__iexact=dept_name)
                data["department_id"] = dept.id
                return data
            except Department.DoesNotExist:
                if not auto_create:
                    # keep old behavior: return helpful 400 to client
                    raise drf_serializers.ValidationError({"department": f"Department '{dept_name}' does not exist."})
                # create department (normalize display name)
                normalized_name = dept_name.title()  # e.g. "water works" -> "Water Works"
                # derive a simple code (lowercase, underscores)
                simple_code = normalized_name.lower().replace(" ", "_")
                dept = Department.objects.create(name=normalized_name, code=simple_code)
                data["department_id"] = dept.id
                return data
    return data

# -----------------------
# Forms
# -----------------------
class AddUserForm(forms.Form):
    username = forms.CharField(max_length=150, required=True, label="Username")
    email = forms.EmailField(required=False, label="Email")
    first_name = forms.CharField(required=False, label="First name")
    last_name = forms.CharField(required=False, label="Last name")
    role = forms.CharField(required=False, label="Role (optional)")
    password = forms.CharField(widget=forms.PasswordInput, min_length=6, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, min_length=6, label="Confirm password")

    def clean_username(self):
        username = self.cleaned_data.get("username").strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def clean(self):
        data = super().clean()
        p1 = data.get("password")
        p2 = data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return data


class SettingsForm(forms.Form):
    default_page_size = forms.IntegerField(min_value=5, max_value=200, initial=25, label='Default page size')
    sla_days = forms.IntegerField(min_value=0, max_value=365, initial=7, label='Default SLA (days)')
    notifications_enabled = forms.BooleanField(required=False, initial=True, label='Enable Notifications')
    notification_email = forms.EmailField(required=False, label='Notification email (from)')


# -----------------------
# Template Views
# -----------------------
@login_required
@never_cache
@user_passes_test(is_admin_user, login_url="accounts:login")
def dashboard_view(request):
    return render(request, "adminpanel/dashboard.html")


@login_required
@never_cache
@user_passes_test(is_admin_user, login_url="accounts:login")
def grievances_list_view(request):
    return render(request, "adminpanel/grievances_list.html")


@login_required
@never_cache
@user_passes_test(is_admin_user, login_url="accounts:login")
def grievance_detail_view(request, pk):
    return render(request, "adminpanel/grievance_detail.html", {"grievance_id": pk})


@login_required
@never_cache
@user_passes_test(is_admin_user, login_url="accounts:login")
def analytics_view(request):
    return render(request, "adminpanel/analytics.html")


@login_required
@never_cache
@user_passes_test(is_admin_user, login_url="accounts:login")
def users_view(request):
    return render(request, "adminpanel/users.html")


@login_required
@never_cache
@user_passes_test(is_admin_user, login_url="accounts:login")
def categories_view(request):
    return render(request, "adminpanel/categories.html")


@login_required
@never_cache
@user_passes_test(is_admin_user, login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def add_user_view(request):
    if request.method == "POST":
        form = AddUserForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                user_kwargs = {
                    "username": data["username"],
                    "email": data.get("email") or "",
                    "first_name": data.get("first_name") or "",
                    "last_name": data.get("last_name") or "",
                }
                user = User.objects.create_user(password=data["password"], **user_kwargs)
                role = data.get("role")
                if role:
                    try:
                        setattr(user, "role", role)
                        user.save(update_fields=["role"])
                    except Exception:
                        pass
                messages.success(request, f"User '{user.username}' created.")
                return redirect("adminpanel:users")
            except Exception as exc:
                logger.exception("Failed to create user: %s", exc)
                form.add_error(None, "Failed to create user. Check server logs for details.")
    else:
        form = AddUserForm()
    return render(request, "adminpanel/add_user.html", {"form": form})


@login_required
@user_passes_test(is_admin_user, login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def edit_user_view(request, pk):
    """
    Server-side view to edit a user (used by admin HTML UI).
    Shows a ModelForm on GET and updates on POST.
    """
    user_obj = get_object_or_404(User, pk=pk)

    class EditUserForm(forms.ModelForm):
        # optional password field: leave blank to keep existing password
        password = forms.CharField(
            required=False,
            widget=forms.PasswordInput,
            label="Password (leave blank to keep current)"
        )

        class Meta:
            model = User
            fields = ["username", "email", "first_name", "last_name"]

        def clean_username(self):
            username = self.cleaned_data.get("username", "").strip()
            if User.objects.exclude(pk=user_obj.pk).filter(username=username).exists():
                raise forms.ValidationError("This username is already taken.")
            return username

        def clean_email(self):
            email = (self.cleaned_data.get("email") or "").strip()
            if email and User.objects.exclude(pk=user_obj.pk).filter(email=email).exists():
                raise forms.ValidationError("This email is already in use.")
            return email

    if request.method == "POST":
        form = EditUserForm(request.POST, instance=user_obj)
        if form.is_valid():
            user = form.save(commit=False)
            pwd = form.cleaned_data.get("password")
            if pwd:
                user.set_password(pwd)
            user.save()
            messages.success(request, f"User {user.username} updated successfully.")
            return redirect("adminpanel:users")
    else:
        form = EditUserForm(instance=user_obj)

    return render(request, "adminpanel/edit_user.html", {"form": form, "user_obj": user_obj})


# -----------------------
# Password Reset (template)
# -----------------------
@never_cache
def reset_password_page(request):
    uidb64 = request.GET.get("uid")
    token = request.GET.get("token")
    if not uidb64 or not token:
        messages.error(request, "Invalid password reset link.")
        return redirect("adminpanel:dashboard")

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except Exception:
        messages.error(request, "Invalid password reset link.")
        return redirect("adminpanel:dashboard")

    if not default_token_generator.check_token(user, token):
        messages.error(request, "Password reset link has expired or is invalid.")
        return redirect("adminpanel:dashboard")

    if request.method == "POST":
        password = request.POST.get("password")
        password2 = request.POST.get("password2")
        if password != password2:
            messages.error(request, "Passwords do not match.")
        elif not password or len(password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
        else:
            user.set_password(password)
            user.save()
            messages.success(request, "Password has been reset successfully. You can now log in.")
            return redirect("accounts:login")

    return render(request, "adminpanel/reset_password_page.html", {"uid": uidb64, "token": token})


# -----------------------
# Settings Page
# -----------------------
@login_required
@user_passes_test(is_admin_user)
@require_http_methods(["GET", "POST"])
def settings_page(request):
    initial = {
        'default_page_size': request.session.get('settings_default_page_size', 25),
        'sla_days': request.session.get('settings_sla_days', 7),
        'notifications_enabled': request.session.get('settings_notifications_enabled', True),
        'notification_email': request.session.get('settings_notification_email', request.user.email),
    }
    if request.method == 'POST':
        form = SettingsForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            request.session['settings_default_page_size'] = data['default_page_size']
            request.session['settings_sla_days'] = data['sla_days']
            request.session['settings_notifications_enabled'] = data['notifications_enabled']
            request.session['settings_notification_email'] = data['notification_email']
            messages.success(request, 'Settings saved (session store).')
            return redirect('adminpanel:settings')
    else:
        form = SettingsForm(initial=initial)
    return render(request, 'adminpanel/settings.html', {'form': form})


# -----------------------
# CSV Export Helper
# -----------------------
class Echo:
    """Object that implements write() for csv.writer to stream."""
    def write(self, value):
        return value


# -----------------------
# API VIEWS (DRF)
# -----------------------

# Categories: list/create
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdminPanel])
def api_categories_list_create(request):
    if request.method == "GET":
        qs = Category.objects.select_related("department").annotate(grievance_count=Count("grievances")).order_by("department__name", "name")
        serializer = CategorySerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    # POST: normalize department (name -> id)
    data = request.data.copy()
    try:
        data = normalize_department(data)
    except drf_serializers.ValidationError as exc:
        return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)

    serializer = CategorySerializer(data=data, context={"request": request})
    if serializer.is_valid():
        obj = serializer.save()
        out = CategorySerializer(Category.objects.filter(pk=obj.pk).annotate(grievance_count=Count("grievances")).first(), context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Category detail: get/update/delete
@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated, IsAdminPanel])
def api_category_detail(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == "GET":
        serializer = CategorySerializer(category, context={"request": request})
        return Response(serializer.data)

    if request.method in ("PUT", "PATCH"):
        partial = request.method == "PATCH"
        data = request.data.copy()
        try:
            data = normalize_department(data)
        except drf_serializers.ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)

        serializer = CategorySerializer(category, data=data, partial=partial, context={"request": request})
        if serializer.is_valid():
            obj = serializer.save()
            out = CategorySerializer(Category.objects.filter(pk=obj.pk).annotate(grievance_count=Count("grievances")).first(), context={"request": request})
            return Response(out.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE: prevent removal if linked grievances exist
    if Grievance.objects.filter(category=category).exists():
        return Response({"detail": "Category has linked grievances and cannot be deleted."}, status=status.HTTP_409_CONFLICT)
    category.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# Grievances: list & create
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdminPanel])
def api_grievances_list(request):
    if request.method == "POST":
        data = request.data.copy()
        try:
            data = normalize_department(data)
        except drf_serializers.ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)

        serializer = GrievanceCreateUpdateSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            obj = serializer.save()
            return Response(GrievanceDetailSerializer(obj, context={"request": request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    qs = Grievance.objects.select_related("user", "category", "department", "assigned_officer").all().order_by("-created_at")

    # Filters (same as you had; supports category id/name etc)
    status_q = request.GET.get("status")
    if status_q:
        qs = qs.filter(status__iexact=status_q)

    category_q = request.GET.get("category")
    if category_q:
        if str(category_q).isdigit():
            qs = qs.filter(category__id=int(category_q))
        else:
            qs = qs.filter(category__name__icontains=category_q)

    assigned_q = request.GET.get("assigned_officer") or request.GET.get("assigned_to") or request.GET.get("assigned")
    if assigned_q and str(assigned_q).isdigit():
        qs = qs.filter(assigned_officer__id=int(assigned_q))

    user_q = request.GET.get("user")
    if user_q and str(user_q).isdigit():
        qs = qs.filter(user__id=int(user_q))

    search = request.GET.get("search")
    if search:
        qs = qs.filter(
            Q(title__icontains=search)
            | Q(description__icontains=search)
            | Q(user__username__icontains=search)
            | Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
        )

    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    if date_from:
        d = parse_date(date_from)
        if d:
            qs = qs.filter(created_at__date__gte=d)
    if date_to:
        d = parse_date(date_to)
        if d:
            qs = qs.filter(created_at__date__lte=d)

    # Pagination-esque: limit/offset
    try:
        limit = int(request.GET.get("limit") or 0)
        offset = int(request.GET.get("offset") or 0)
    except ValueError:
        limit = 0
        offset = 0

    total = qs.count()
    if limit > 0:
        qs = qs[offset: offset + limit]
    else:
        qs = qs[offset: offset + 100]

    serializer = GrievanceListSerializer(qs, many=True, context={"request": request})
    return Response({"count": total, "results": serializer.data})


# Grievance detail: get/update/delete
@api_view(["GET", "PATCH", "PUT", "DELETE"])
@permission_classes([IsAuthenticated, IsAdminPanel])
def api_grievance_detail(request, pk):
    grievance = get_object_or_404(Grievance, pk=pk)

    if request.method == "GET":
        serializer = GrievanceDetailSerializer(grievance, context={"request": request})
        return Response(serializer.data)

    if request.method in ("PATCH", "PUT"):
        partial = request.method == "PATCH"
        data = request.data.copy()
        try:
            data = normalize_department(data)
        except drf_serializers.ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)

        serializer = GrievanceCreateUpdateSerializer(grievance, data=data, partial=partial, context={"request": request})
        if serializer.is_valid():
            before_status = grievance.status
            before_assigned = getattr(grievance.assigned_officer, "pk", None)

            updated = serializer.save()

            if before_status != updated.status:
                ChangeLog.objects.create(
                    user=request.user,
                    grievance=updated,
                    action="status_changed",
                    before=str(before_status),
                    after=str(updated.status),
                )

            after_assigned = getattr(updated.assigned_officer, "pk", None)
            if str(before_assigned) != str(after_assigned):
                ChangeLog.objects.create(
                    user=request.user,
                    grievance=updated,
                    action="assigned_officer_changed",
                    before=str(before_assigned),
                    after=str(after_assigned),
                )

            return Response(GrievanceDetailSerializer(updated, context={"request": request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE guard: cannot delete if feedback or resolved
    if getattr(grievance, "feedback", None) or grievance.status == Grievance.STATUS_RESOLVED:
        return Response({"detail": "Cannot delete a grievance that has feedback or is resolved."}, status=status.HTTP_400_BAD_REQUEST)
    grievance.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# Assign grievance to officer
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminPanel])
def api_grievance_assign(request, pk):
    grievance = get_object_or_404(Grievance, pk=pk)
    officer_id = request.data.get("assigned_officer") or request.data.get("assigned_to") or request.data.get("assigned")
    if not officer_id:
        return Response({"detail": "assigned_officer is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        officer = User.objects.get(pk=int(officer_id))
    except (User.DoesNotExist, ValueError):
        return Response({"detail": "Officer not found"}, status=status.HTTP_404_NOT_FOUND)

    is_officer = getattr(officer, "role", None) == "officer" or officer.is_staff or officer.is_superuser
    if not is_officer:
        return Response({"detail": "Selected user is not an officer"}, status=status.HTTP_400_BAD_REQUEST)

    before_assigned = getattr(grievance.assigned_officer, "pk", None)
    grievance.assigned_officer = officer
    grievance.save()

    ChangeLog.objects.create(
        user=request.user,
        grievance=grievance,
        action="assigned_officer",
        before=str(before_assigned),
        after=str(getattr(officer, "pk", None)),
    )

    serializer = GrievanceDetailSerializer(grievance, context={"request": request})
    return Response(serializer.data, status=status.HTTP_200_OK)


# Add remark to grievance
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminPanel])
def api_grievance_add_remark(request, pk):
    grievance = get_object_or_404(Grievance, pk=pk)
    text = request.data.get("remark") or request.data.get("comment") or request.data.get("text")
    if not text:
        return Response({"detail": "remark text required"}, status=status.HTTP_400_BAD_REQUEST)

    remark = GrievanceRemark.objects.create(grievance=grievance, officer=request.user, remark=text)
    serializer = GrievanceRemarkSerializer(remark, context={"request": request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)


# Analytics summary
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminPanel])
def api_analytics(request):
    total = Grievance.objects.count()

    status_qs = Grievance.objects.values("status").annotate(count=Count("id"))
    by_status = {item["status"]: item["count"] for item in status_qs}

    cat_qs = Category.objects.annotate(count=Count("grievances")).filter(count__gt=0).order_by("-count")
    by_category = [{"id": c.id, "name": c.name, "count": c.count} for c in cat_qs]

    resolved_qs = Grievance.objects.filter(status=Grievance.STATUS_RESOLVED).annotate(
        resolution_time=F("updated_at") - F("created_at")
    ).values_list("resolution_time", flat=True)

    avg_days = None
    times = list(resolved_qs)
    if times:
        total_seconds = sum([t.total_seconds() if hasattr(t, "total_seconds") else 0 for t in times])
        avg_days = round((total_seconds / len(times)) / 86400, 2)

    return Response({
        "total_grievances": total,
        "by_status": by_status,
        "by_category": by_category,
        "avg_resolution_days": avg_days,
    })


# Export CSV (streaming)
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminPanel])
def api_export_grievances_csv(request):
    qs = Grievance.objects.select_related('user', 'category', 'department', 'assigned_officer').order_by('-created_at')

    # apply filters similar to list endpoint
    status_q = request.GET.get("status")
    if status_q:
        qs = qs.filter(status__iexact=status_q)

    category_q = request.GET.get("category")
    if category_q:
        if str(category_q).isdigit():
            qs = qs.filter(category__id=int(category_q))
        else:
            qs = qs.filter(category__name__icontains=category_q)

    assigned_q = request.GET.get("assigned_officer") or request.GET.get("assigned_to") or request.GET.get("assigned")
    if assigned_q and str(assigned_q).isdigit():
        qs = qs.filter(assigned_officer__id=int(assigned_q))

    search = request.GET.get("search")
    if search:
        qs = qs.filter(
            Q(title__icontains=search)
            | Q(description__icontains=search)
            | Q(user__username__icontains=search)
            | Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
        )

    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    if date_from:
        d = parse_date(date_from)
        if d:
            qs = qs.filter(created_at__date__gte=d)
    if date_to:
        d = parse_date(date_to)
        if d:
            qs = qs.filter(created_at__date__lte=d)

    export_all = request.GET.get('export_all') == '1'
    if not export_all:
        try:
            limit = int(request.GET.get('limit') or 100)
        except ValueError:
            limit = 100
        try:
            offset = int(request.GET.get('offset') or 0)
        except ValueError:
            offset = 0
        qs = qs[offset: offset + limit]

    def row_iter():
        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)
        yield writer.writerow([
            'id','tracking_id','title','description','status','category','department',
            'user_id','username','assigned_officer_id','assigned_officer_username',
            'created_at','updated_at'
        ]).encode('utf-8')
        for g in qs.iterator():
            yield writer.writerow([
                smart_str(g.id),
                smart_str(g.tracking_id),
                smart_str(g.title),
                smart_str(g.description),
                smart_str(g.status),
                smart_str(getattr(g.category, 'name', '') if g.category else ''),
                smart_str(getattr(g.department, 'name', '') if g.department else ''),
                smart_str(getattr(g.user, 'id', '')),
                smart_str(getattr(g.user, 'username', '')),
                smart_str(getattr(g.assigned_officer, 'id', '')),
                smart_str(getattr(g.assigned_officer, 'username', '')),
                smart_str(g.created_at.isoformat() if g.created_at else ''),
                smart_str(g.updated_at.isoformat() if g.updated_at else ''),
            ]).encode('utf-8')

    filename = "grievances_export.csv"
    resp = StreamingHttpResponse(row_iter(), content_type="text/csv; charset=utf-8")
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    return resp


# User status (officers list for selects)
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminPanel])
def api_user_status(request):
    qs = User.objects.filter(role='officer').order_by('username')
    officers = [
        {
            'id': u.id,
            'username': u.username,
            'full_name': u.get_full_name(),
            'email': u.email,
        }
        for u in qs
    ]
    return Response({'officers': officers})


# Admin create user serializer & list/create API (kept concise)
class AdminCreateUserSerializer(drf_serializers.Serializer):
    username = drf_serializers.CharField(max_length=150)
    email = drf_serializers.EmailField(required=False, allow_blank=True)
    first_name = drf_serializers.CharField(required=False, allow_blank=True)
    last_name = drf_serializers.CharField(required=False, allow_blank=True)
    role = drf_serializers.CharField(required=False, allow_blank=True)
    password = drf_serializers.CharField(write_only=True, min_length=6)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise drf_serializers.ValidationError("Username already in use.")
        return value

    def validate_email(self, value):
        if value and User.objects.filter(email=value).exists():
            raise drf_serializers.ValidationError("Email already in use.")
        return value

    def create(self, validated_data):
        pwd = validated_data.pop("password")
        role = validated_data.pop("role", None)
        user = User.objects.create_user(password=pwd, **validated_data)
        if role:
            try:
                setattr(user, "role", role)
                user.save(update_fields=["role"])
            except Exception:
                pass
        return user


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdminPanel])
def api_users_list_create(request):
    # GET
    if request.method == "GET":
        try:
            page = max(int(request.GET.get("page", 1)), 1)
            page_size = max(int(request.GET.get("page_size", 25)), 1)
        except ValueError:
            page, page_size = 1, 25

        qs = User.objects.all().order_by("username")

        role = request.GET.get("role")
        if role:
            if hasattr(User, "_meta") and any(f.name == "role" for f in User._meta.get_fields()):
                qs = qs.filter(**{"role": role})
            else:
                logger.warning("api_users_list_create: requested role filter but User model has no 'role' field.")

        status_param = request.GET.get("status")
        if status_param:
            if status_param.lower() in ("active", "true", "1"):
                qs = qs.filter(is_active=True)
            elif status_param.lower() in ("inactive", "false", "0"):
                qs = qs.filter(is_active=False)

        search = (request.GET.get("search") or "").strip()
        if search:
            qs = qs.filter(
                Q(username__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
            )

        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size
        items = qs[start:end]

        data = [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "role": getattr(u, "role", None),
                "is_active": getattr(u, "is_active", False),
                "last_login": getattr(u, "last_login", None),
            }
            for u in items
        ]
        return Response({"count": total, "results": data})

    # POST -> create
    serializer = AdminCreateUserSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = serializer.save()
    except Exception as exc:
        logger.exception("api_users_list_create: create failed: %s", exc)
        return Response({"detail": "Failed to create user"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": getattr(user, "role", None),
    }, status=status.HTTP_201_CREATED)


# User detail API (get/patch/put/delete)
@api_view(["GET", "PATCH", "PUT", "DELETE"])
@permission_classes([IsAuthenticated, IsAdminPanel])
def api_user_detail(request, pk):
    user_obj = get_object_or_404(User, pk=pk)

    class UserUpdateSerializer(drf_serializers.ModelSerializer):
        password = drf_serializers.CharField(write_only=True, required=False, allow_blank=True, min_length=6)

        class Meta:
            model = User
            fields = ["username", "email", "first_name", "last_name", "role", "is_active", "password"]

        def update(self, instance, validated_data):
            pwd = validated_data.pop("password", None)
            for attr, val in validated_data.items():
                setattr(instance, attr, val)
            if pwd:
                instance.set_password(pwd)
            instance.save()
            return instance

    if request.method == "GET":
        data = {
            "id": user_obj.id,
            "username": user_obj.username,
            "email": user_obj.email,
            "first_name": user_obj.first_name,
            "last_name": user_obj.last_name,
            "role": getattr(user_obj, "role", None),
            "is_active": user_obj.is_active,
        }
        return Response(data)

    if request.method in ("PATCH", "PUT"):
        partial = request.method == "PATCH"
        serializer = UserUpdateSerializer(user_obj, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "DELETE":
        user_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Password reset email (admin triggers)
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminPanel])
def api_user_send_reset(request, pk):
    user_obj = get_object_or_404(User, pk=pk)

    if not user_obj.email:
        return Response({"detail": "Target user has no email address."}, status=status.HTTP_400_BAD_REQUEST)

    uid = urlsafe_base64_encode(force_bytes(user_obj.pk))
    token = default_token_generator.make_token(user_obj)

    frontend_base = getattr(settings, "FRONTEND_PASSWORD_RESET_URL", None)
    if frontend_base:
        reset_url = f"{frontend_base.rstrip('?&')}?uid={uid}&token={token}"
    else:
        reset_path = reverse('adminpanel:reset_password_page')
        reset_url = request.build_absolute_uri(f"{reset_path}?uid={uid}&token={token}")

    subject = getattr(settings, "PASSWORD_RESET_SUBJECT", "Password reset for your account")
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")

    context = {
        "user": user_obj,
        "reset_url": reset_url,
        "site_name": getattr(settings, "SITE_NAME", "Grievance Portal"),
    }
    try:
        text_body = render_to_string("emails/password_reset.txt", context)
    except Exception:
        text_body = f"Reset your password by visiting: {reset_url}"

    try:
        html_body = render_to_string("emails/password_reset.html", context)
    except Exception:
        html_body = None

    try:
        msg = EmailMultiAlternatives(subject=subject, body=text_body, from_email=from_email, to=[user_obj.email])
        if html_body:
            msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
    except Exception as exc:
        logger.exception("api_user_send_reset: failed to send email to %s: %s", user_obj.email, exc)
        return Response({"detail": "Failed to send email", "error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"detail": "Password reset link sent"}, status=status.HTTP_200_OK)


# API password reset confirm (for SPA / API-driven flow)
@api_view(["POST"])
@permission_classes([AllowAny])
def api_password_reset_confirm(request):
    uid = request.data.get("uid")
    token = request.data.get("token")
    new_password = request.data.get("new_password")

    if not uid or not token or not new_password:
        return Response({"detail": "uid, token and new_password are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        uid_decoded = urlsafe_base64_decode(uid).decode()
        user = User.objects.get(pk=uid_decoded)
    except Exception:
        return Response({"detail": "Invalid uid."}, status=status.HTTP_400_BAD_REQUEST)

    if not default_token_generator.check_token(user, token):
        return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user.set_password(new_password)
        user.save()
    except Exception as exc:
        logger.exception("api_password_reset_confirm: failed to set password: %s", exc)
        return Response({"detail": "Failed to reset password."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"detail": "Password reset successfully."}, status=status.HTTP_200_OK)


# Dev-only debug endpoint (remove in production)
@login_required
@user_passes_test(is_admin_user)
def debug_request_inspect(request):
    meta_sample = {k: request.META.get(k) for k in ('HTTP_COOKIE', 'HTTP_AUTHORIZATION', 'HTTP_HOST', 'HTTP_ORIGIN')}
    cookies = dict(request.COOKIES)
    user_info = {
        'is_authenticated': getattr(request, 'user', None) and request.user.is_authenticated,
        'username': getattr(request.user, 'username', None)
    }
    return JsonResponse({'meta': meta_sample, 'cookies': cookies, 'user': user_info})
