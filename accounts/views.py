# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from .forms import RegisterForm
from django.contrib.auth.views import LoginView, LogoutView
from django.views.decorators.csrf import csrf_protect
from django.urls import reverse_lazy
from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseForbidden

# DRF imports
from rest_framework import generics, viewsets, permissions, status
from rest_framework.response import Response
from .serializers import RegisterSerializer, UserSerializer
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
def register_view(request):
    """
    HTML registration view. Registration form does NOT accept or expose role.
    New users are assigned role='citizen' server-side.
    """
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            # create user but do not let user choose role
            user = form.save(commit=False)
            # force the role to 'citizen' — registration does not accept other roles
            if hasattr(user, "role"):
                user.role = "citizen"
            user.is_active = True
            user.save()
            messages.success(request, "Account created. Please log in.")
            return redirect("accounts:login")
        else:
            # Debug print and user-friendly message handling
            print("Register form errors:", form.errors)
            username_errors = form.errors.get('username')
            if username_errors and any('already exists' in str(e).lower() for e in username_errors):
                messages.error(request, "That username is already taken. Please choose a different username.")
            else:
                messages.error(request, "Please correct the errors below and try again.")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


# ---------- DRF API views (unchanged) ----------
class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if isinstance(response.data, dict) and 'password' in response.data:
            response.data.pop('password', None)
        return response


class MeAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [IsAdminPanel]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        headers = self.get_success_headers(serializer.data)
        data = serializer.data.copy()
        data.pop('password', None)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)
