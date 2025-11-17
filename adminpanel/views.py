# adminpanel/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import user_passes_test

# DRF imports for function-based APIs
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils.dateparse import parse_date
from django.db.models import Q

# local models & serializers
from adminpanel.models import Category, Grievance, GrievanceRemark
from .serializers import (
    CategorySerializer,
    GrievanceListSerializer,
    GrievanceDetailSerializer,
    GrievanceRemarkSerializer,
)
from django.contrib.auth import get_user_model
from accounts.permissions import IsAdminPanel

User = get_user_model()


# -----------------------
# Helper: admin check for template views
# -----------------------
def is_admin_user(user):
    """
    True for staff/superuser or user.role == 'admin'.
    Adjust to your project's role field if different.
    """
    return user.is_authenticated and (user.is_staff or user.is_superuser or getattr(user, "role", None) == "admin")


# -----------------------
# TEMPLATE (HTML) VIEWS
# -----------------------
@user_passes_test(is_admin_user, login_url="accounts:login")
def dashboard_view(request):
    """Renders admin dashboard page."""
    return render(request, "adminpanel/dashboard.html")


@user_passes_test(is_admin_user, login_url="accounts:login")
def grievances_list_view(request):
    """Renders grievances list page."""
    return render(request, "adminpanel/grievances_list.html")


@user_passes_test(is_admin_user, login_url="accounts:login")
def grievance_detail_view(request, pk):
    """Renders grievance detail page. Template may fetch details via API."""
    return render(request, "adminpanel/grievance_detail.html", {"grievance_id": pk})


@user_passes_test(is_admin_user, login_url="accounts:login")
def analytics_view(request):
    """Renders analytics page."""
    return render(request, "adminpanel/analytics.html")


@user_passes_test(is_admin_user, login_url="accounts:login")
def users_view(request):
    """Renders users management page."""
    return render(request, "adminpanel/users.html")


@user_passes_test(is_admin_user, login_url="accounts:login")
def categories_view(request):
    """Renders categories management page."""
    return render(request, "adminpanel/categories.html")


# -----------------------
# API VIEWS (function-based; serializer-driven)
# -----------------------

# Categories: list & create
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdminPanel])
def api_categories_list_create(request):
    if request.method == "GET":
        qs = Category.objects.select_related("department").order_by("department__name", "name")
        serializer = CategorySerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    # POST -> create
    serializer = CategorySerializer(data=request.data, context={"request": request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Category detail: get / put / patch / delete
@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated, IsAdminPanel])
def api_category_detail(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == "GET":
        serializer = CategorySerializer(category, context={"request": request})
        return Response(serializer.data)

    if request.method in ("PUT", "PATCH"):
        partial = request.method == "PATCH"
        serializer = CategorySerializer(category, data=request.data, partial=partial, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE
    category.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# Grievances list (with simple filters)
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminPanel])
def api_grievances_list(request):
    qs = Grievance.objects.select_related("user", "category", "department", "assigned_officer").all().order_by("-created_at")

    # filters
    status_q = request.GET.get("status")
    if status_q:
        qs = qs.filter(status__iexact=status_q)

    category_q = request.GET.get("category")
    if category_q:
        if category_q.isdigit():
            qs = qs.filter(category__id=int(category_q))
        else:
            qs = qs.filter(category__name__icontains=category_q)

    assigned_q = request.GET.get("assigned_officer") or request.GET.get("assigned_to") or request.GET.get("assigned")
    if assigned_q and assigned_q.isdigit():
        qs = qs.filter(assigned_officer__id=int(assigned_q))

    user_q = request.GET.get("user")
    if user_q and user_q.isdigit():
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

    # pagination: ?limit=20&offset=0
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
        qs = qs[offset : offset + 100]  # safe default cap

    serializer = GrievanceListSerializer(qs, many=True, context={"request": request})
    return Response({"count": total, "results": serializer.data})


# Grievance assign (action)
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

    grievance.assigned_officer = officer
    grievance.save()

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

