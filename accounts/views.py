# accounts/views.py
# accounts/views.py (top imports)
import threading
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_protect
from django.urls import reverse_lazy
from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseForbidden
from django.contrib.auth.views import LoginView, LogoutView

# DRF imports
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.response import Response

# local imports
from .forms import RegisterForm    # your registration form
from .serializers import RegisterSerializer, UserSerializer, AdminCreateUserSerializer
from .permissions import IsAdminPanel
from accounts.utils.email_smtp import send_via_smtplib  # <-- use accounts utils
# remove any `from adminpanel.utils.email_smtp` duplicate imports


# DRF imports - using plain APIView (no generics/viewsets)
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.response import Response

from .serializers import RegisterSerializer, UserSerializer, AdminCreateUserSerializer  # AdminCreateUserSerializer: add this if not present
from .permissions import IsAdminPanel

User = get_user_model()


# ---------- Role mixin (reusable) ----------
class RoleRequiredMixin(UserPassesTestMixin):
    """
    Mix-in to require a role for views. Set allowed_roles = ('citizen','officer','admin')
    Staff/superuser bypass role checks (treated as admin).
    """
    allowed_roles = ()

    def test_func(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
            return True
        return getattr(user, 'role', None) in self.allowed_roles

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        return HttpResponseForbidden("Access denied: insufficient role privileges.")


# ---------- Login / Logout (role-based redirect) ----------
class CustomLoginView(LoginView):
    """
    LoginView that redirects users to role-specific dashboards after login.
    Honors safe 'next' parameter first; otherwise maps role -> dashboard.
    """
    template_name = 'accounts/login.html'

    ROLE_REDIRECT_MAP = {
        'admin': reverse_lazy('adminpanel:dashboard'),
        'officer': reverse_lazy('officer:dashboard'),
        'citizen': reverse_lazy('citizen:dashboard'),
    }

    def form_valid(self, form):
        # Log the user in (super does this)
        response = super().form_valid(form)

        # 1) if a safe 'next' param present, redirect there
        redirect_to = self.get_redirect_url()
        if redirect_to:
            allowed = url_has_allowed_host_and_scheme(
                url=redirect_to,
                allowed_hosts={self.request.get_host(), *getattr(settings, "ALLOWED_HOSTS", [])},
                require_https=self.request.is_secure()
            )
            if allowed:
                return redirect(redirect_to)

        # 2) else route by role/staff/superuser
        user = self.request.user
        if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
            return redirect(self.ROLE_REDIRECT_MAP['admin'])

        user_role = getattr(user, 'role', None)
        if user_role and user_role in self.ROLE_REDIRECT_MAP:
            return redirect(self.ROLE_REDIRECT_MAP[user_role])

        # 3) fallback
        return redirect(getattr(settings, "LOGIN_REDIRECT_URL", "/"))


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('accounts:login')


# ---------- Registration (no role input) ----------
@csrf_protect

@csrf_protect
def register_view(request):
    """
    Registration view — creates user and sends welcome email via smtplib (background thread).
    Uses RegisterForm defined in accounts/forms.py
    """
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Adjust field name if your form uses password1/password2
            pwd = form.cleaned_data.get("password") or form.cleaned_data.get("password1")
            if pwd:
                user.set_password(pwd)
            user.is_active = True
            user.save()

            # Prepare email content
            subject = "Welcome to Kerala Grievance Portal"
            plain = (
                f"Hello {user.get_full_name() or user.username},\n\n"
                "Welcome to the Kerala Grievance Portal. Your account has been created successfully.\n\n"
                "You can login at: /accounts/login/\n\n"
                "Regards,\nGrievance Portal Team"
            )

            # Render HTML template safely (optional)
            try:
                html = render_to_string("emails/welcome.html", {"user": user, "site_name": "Kerala Grievance Portal"}, request=request)
            except Exception:
                html = None

            # Send in background thread (non-blocking)
            def _send():
                result = send_via_smtplib(
                    to_email=user.email,
                    subject=subject,
                    plain_text=plain,
                    html=html,
                )
                if not result.get("ok"):
                    logging.getLogger(__name__).warning("Registration email failed: %s", result)

            try:
                t = threading.Thread(target=_send, daemon=True)
                t.start()
            except Exception:
                # fallback: synchronous send
                send_via_smtplib(to_email=user.email, subject=subject, plain_text=plain, html=html)

            messages.success(request, "Registration successful. A welcome email will be sent shortly.")
            return redirect("accounts:login")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})

# -------------------------
# Plain REST API endpoints
# -------------------------

class RegisterAPI(APIView):
    """
    POST: register new user (public)
    Uses RegisterSerializer which requires password + password2
    """
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            # serializer.create handles role assignment
            user = serializer.save()
            out = UserSerializer(user).data
            return Response(out, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MeAPI(APIView):
    """
    GET: retrieve current user
    PATCH: update current user (partial)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, format=None):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminUserListCreateAPI(APIView):
    """
    Admin-only:
    GET: list users
    POST: create user (admin supplies password)
    """
    permission_classes = [IsAuthenticated, IsAdminPanel]

    def get(self, request, format=None):
        users = User.objects.all().order_by('-date_joined')
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        # Expecting AdminCreateUserSerializer to be present in serializers.py
        # If not present, you can use a similar serializer that handles `password` with set_password.
        try:
            serializer = AdminCreateUserSerializer(data=request.data)
        except NameError:
            # fallback: try to reuse RegisterSerializer but it requires password2.
            # Ask admin to provide password2 as same as password if using RegisterSerializer.
            serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            out = UserSerializer(user).data
            return Response(out, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminUserDetailAPI(APIView):
    """
    Admin-only:
    GET / PATCH / DELETE for a single user identified by pk
    """
    permission_classes = [IsAuthenticated, IsAdminPanel]

    def get_object(self, pk):
        return get_object_or_404(User, pk=pk)

    def get(self, request, pk, format=None):
        user = self.get_object(pk)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk, format=None):
        user = self.get_object(pk)
        # prefer AdminCreateUserSerializer for password handling
        try:
            serializer = AdminCreateUserSerializer(user, data=request.data, partial=True)
        except NameError:
            serializer = UserSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            # If serializer doesn't handle password properly, ensure to call set_password manually
            updated = serializer.save()
            # If raw password provided in request and serializer didn't handle it:
            raw_pwd = request.data.get('password')
            if raw_pwd and not hasattr(updated, 'password') or not updated.check_password(raw_pwd):
                updated.set_password(raw_pwd)
                updated.save()
            return Response(UserSerializer(updated).data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        user = self.get_object(pk)
        # protection: prevent deleting superuser or deleting self
        if user.is_superuser:
            return Response({"detail": "Cannot delete superuser."}, status=status.HTTP_403_FORBIDDEN)
        if user == request.user:
            return Response({"detail": "You cannot delete your own account."}, status=status.HTTP_403_FORBIDDEN)

        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

