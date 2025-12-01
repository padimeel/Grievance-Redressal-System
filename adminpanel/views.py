# adminpanel/views.py
from django.shortcuts import render, get_object_or_404, redirect   # added redirect
from django.contrib.auth.decorators import user_passes_test, login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods     # <<-- add this
from django.db.models import Q, Count, F
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django import forms 
from .forms import SettingsForm

# DRF imports
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

# Local models & serializers
from adminpanel.models import Category, Grievance, GrievanceRemark, ChangeLog
from .serializers import (
    CategorySerializer,
    GrievanceListSerializer,
    GrievanceDetailSerializer,
    GrievanceCreateUpdateSerializer,
    GrievanceRemarkSerializer,
)
from accounts.permissions import IsAdminPanel

User = get_user_model()


# -----------------------
# Helper: admin check
# -----------------------
def is_admin_user(user):
    """True for staff/superuser or user.role == 'admin'."""
    return user.is_authenticated and (
        getattr(user, "is_staff", False)
        or getattr(user, "is_superuser", False)
        or getattr(user, "role", None) == "admin"
    )


# -----------------------
# TEMPLATE VIEWS
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


# -----------------------
# API VIEWS
# -----------------------

# Categories: list & create
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdminPanel])
def api_categories_list_create(request):
    if request.method == "GET":
        qs = Category.objects.select_related("department").order_by(
            "department__name", "name"
        )
        serializer = CategorySerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    serializer = CategorySerializer(data=request.data, context={"request": request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Category detail
@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated, IsAdminPanel])
def api_category_detail(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == "GET":
        serializer = CategorySerializer(category, context={"request": request})
        return Response(serializer.data)

    if request.method in ("PUT", "PATCH"):
        partial = request.method == "PATCH"
        serializer = CategorySerializer(
            category, data=request.data, partial=partial, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if Grievance.objects.filter(category=category).exists():
        return Response(
            {"detail": "Category has linked grievances and cannot be deleted."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    category.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# Grievances list
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdminPanel])
def api_grievances_list(request):
    if request.method == "POST":
        serializer = GrievanceCreateUpdateSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            obj = serializer.save()
            return Response(
                GrievanceDetailSerializer(obj, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    qs = Grievance.objects.select_related(
        "user", "category", "department", "assigned_officer"
    ).all().order_by("-created_at")

    # Filters
    status_q = request.GET.get("status")
    if status_q:
        qs = qs.filter(status__iexact=status_q)

    category_q = request.GET.get("category")
    if category_q:
        if str(category_q).isdigit():
            qs = qs.filter(category__id=int(category_q))
        else:
            qs = qs.filter(category__name__icontains=category_q)

    assigned_q = request.GET.get("assigned_officer") or request.GET.get(
        "assigned_to"
    ) or request.GET.get("assigned")
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

    # Pagination
    try:
        limit = int(request.GET.get("limit") or 0)
        offset = int(request.GET.get("offset") or 0)
    except ValueError:
        limit = 0
        offset = 0

    total = qs.count()
    if limit > 0:
        qs = qs[offset : offset + limit]
    else:
        qs = qs[offset : offset + 100]

    serializer = GrievanceListSerializer(qs, many=True, context={"request": request})
    return Response({"count": total, "results": serializer.data})


# Grievance assign
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminPanel])
def api_grievance_assign(request, pk):
    grievance = get_object_or_404(Grievance, pk=pk)
    officer_id = (
        request.data.get("assigned_officer")
        or request.data.get("assigned_to")
        or request.data.get("assigned")
    )

    if not officer_id:
        return Response(
            {"detail": "assigned_officer is required"}, status=status.HTTP_400_BAD_REQUEST
        )

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


# Add remark
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


# Grievance detail
@api_view(["GET", "PATCH", "PUT", "DELETE"])
@permission_classes([IsAuthenticated, IsAdminPanel])
def api_grievance_detail(request, pk):
    grievance = get_object_or_404(Grievance, pk=pk)

    if request.method == "GET":
        serializer = GrievanceDetailSerializer(grievance, context={"request": request})
        return Response(serializer.data)

    if request.method in ("PATCH", "PUT"):
        partial = request.method == "PATCH"
        serializer = GrievanceCreateUpdateSerializer(
            grievance, data=request.data, partial=partial, context={"request": request}
        )
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

    if getattr(grievance, "feedback", None) or grievance.status == Grievance.STATUS_RESOLVED:
        return Response(
            {"detail": "Cannot delete a grievance that has feedback or is resolved."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    grievance.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# Analytics
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


# User status for dropdowns
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminPanel])
def api_user_status(request):
    """
    Return a minimal list of *officer* users for select controls.
    Only users with role == 'officer' are returned.
    """
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

# -----------------------
# Dev-only debug endpoint (remove in production)

@login_required
@user_passes_test(is_admin_user)
def grievance_detail(request, pk):

    g = get_object_or_404(Grievance.objects.select_related('category','user','assigned_officer'), pk=pk)
    # simple status update form inline
    if request.method == 'POST':
        status = request.POST.get('status')
        remark = request.POST.get('remark','').strip()
        if status and status in dict(Grievance.STATUS_CHOICES):
            g.status = status
            if remark:
                # append remark as a simple text field; replace with proper remarks model if you have one
                if hasattr(g, 'remarks'):
                    g.remarks = (g.remarks or '') + f"\n[{request.user.username}] {remark}"
                else:
                    # you can add a remarks TextField to Grievance model later
                    pass
            g.save()
            messages.success(request, 'Status updated.')
            # TODO: trigger notifications here (email/sms)
            return redirect('adminpanel:grievance-detail', pk=pk)
        else:
            messages.error(request, 'Invalid status selected.')
    return render(request, 'admin/grievance_detail.html', {'g': g, 'statuses': Grievance.STATUS_CHOICES})

# -----------------------
@csrf_exempt
def debug_request_inspect(request):
    """
    Dev helper: return cookies and user authentication status.
    Add a URL mapping to use this while debugging.
    Remove this view in production.
    """
    meta_sample = {k: request.META.get(k) for k in (
        'HTTP_COOKIE', 'HTTP_AUTHORIZATION', 'HTTP_HOST', 'HTTP_ORIGIN'
    )}
    cookies = dict(request.COOKIES)
    user_info = {
        'is_authenticated': getattr(request, 'user', None) and request.user.is_authenticated,
        'username': getattr(request.user, 'username', None)
    }
    return JsonResponse({'meta': meta_sample, 'cookies': cookies, 'user': user_info})
class SettingsForm(forms.Form):
    default_page_size = forms.IntegerField(min_value=5, max_value=200, initial=25, label='Default page size')
    sla_days = forms.IntegerField(min_value=0, max_value=365, initial=7, label='Default SLA (days)')
    notifications_enabled = forms.BooleanField(required=False, initial=True, label='Enable Notifications')
    notification_email = forms.EmailField(required=False, label='Notification email (from)')

@login_required
@user_passes_test(is_admin_user)
@require_http_methods(["GET","POST"])
def settings_page(request):
    # TODO: replace with real DB-backed settings; for now read/write from session as quick store
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
            messages.success(request, 'Settings saved (session store). For persistent settings, create a SiteSettings model.');
            return redirect('adminpanel:settings')
    else:
        form = SettingsForm(initial=initial)
    return render(request, 'adminpanel/settings.html', {'form': form})
# Replace the existing SettingsForm in adminpanel/views.py with this version
from django import forms

class SettingsForm(forms.Form):
    default_page_size = forms.IntegerField(
        min_value=5,
        max_value=200,
        initial=25,
        label='Default page size',
        widget=forms.NumberInput(attrs={
            'class': 'w-28 px-3 py-2 border rounded',
            'aria-label': 'Default page size'
        })
    )

    sla_days = forms.IntegerField(
        min_value=0,
        max_value=365,
        initial=7,
        label='Default SLA (days)',
        widget=forms.NumberInput(attrs={
            'class': 'w-28 px-3 py-2 border rounded',
            'aria-label': 'Default SLA (days)'
        })
    )

    notifications_enabled = forms.BooleanField(
        required=False,
        initial=True,
        label='Enable Notifications',
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500',
            'aria-label': 'Enable notifications'
        })
    )

    notification_email = forms.EmailField(
        required=False,
        label='Notification email (from)',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border rounded',
            'placeholder': 'no-reply@example.com',
            'aria-label': 'Notification email'
        })
    )


