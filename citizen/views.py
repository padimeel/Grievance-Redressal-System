# backend/citizen/views.py
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, CreateView, DetailView
from django import forms
from rest_framework import viewsets, permissions
from .serializers import FeedbackSerializer
from .models import Grievance, Category,Feedback

# Optional role mixin import (if you have it in accounts.views)
try:
    from accounts.views import RoleRequiredMixin
except Exception:
    RoleRequiredMixin = type("RoleRequiredMixin", (UserPassesTestMixin,), {
        "allowed_roles": ("citizen",),
        "test_func": lambda self: self.request.user.is_authenticated and getattr(self.request.user, "role", None) in ("citizen", "officer", "admin"),
        "handle_no_permission": lambda self: redirect('accounts:login')
    })


class CitizenDashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard for a citizen. Shows recent grievances and simple statistics.
    Template: templates/citizen/dashboard.html
    Context variables provided:
      - recent_grievances: last 6 grievances for the user
      - total_open: count of grievances not resolved/closed
      - total_all: total grievances for the user
    """
    template_name = 'citizen/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        # For officers/admin, you might want different dashboard; this is citizen focused
        if user.is_authenticated and (user.is_staff or user.is_superuser or getattr(user, 'role', None) in ('officer', 'admin')):
            # if an officer/admin visits this view we show overall stats (optional)
            recent = Grievance.objects.all().select_related('category', 'user').order_by('-created_at')[:6]
            total_open = Grievance.objects.exclude(status__in=('resolved', 'closed')).count()
            total_all = Grievance.objects.count()
        else:
            recent = Grievance.objects.filter(user=user).select_related('category').order_by('-created_at')[:6]
            total_open = Grievance.objects.filter(user=user).exclude(status__in=('resolved', 'closed')).count()
            total_all = Grievance.objects.filter(user=user).count()

        ctx.update({
            'recent_grievances': recent,
            'total_open': total_open,
            'total_all': total_all,
        })
        return ctx


# Inline ModelForm to avoid adding a new file; move to forms.py if you prefer
class GrievanceForm(forms.ModelForm):
    # Accept category_name as extra optional input
    category_name = forms.CharField(label='Category (new)', required=False,
                                    help_text='Type a category name to create it if it does not exist.')

    class Meta:
        model = Grievance
        fields = ['title', 'description', 'attachment', 'category', 'category_name']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned = super().clean()
        cat = cleaned.get('category')
        cat_name = cleaned.get('category_name')
        # if both empty -> ok (category optional), if category provided ignore name
        if not cat and cat_name:
            cleaned['category_name'] = cat_name.strip()
        return cleaned


class GrievanceListView(LoginRequiredMixin, ListView):
    """
    List grievances belonging to the logged-in user.
    Template: templates/citizen/grievance_list.html
    """
    model = Grievance
    template_name = 'citizen/grievance_list.html'
    context_object_name = 'grievances'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        # officers/admin can see all grievances (optionally)
        if user.is_staff or user.is_superuser or getattr(user, 'role', None) in ('officer', 'admin'):
            return Grievance.objects.all().select_related('category', 'user').order_by('-created_at')
        return Grievance.objects.filter(user=user).select_related('category').order_by('-created_at')


class GrievanceCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new grievance. If category_name provided, create Category automatically.
    Template: templates/citizen/grievance_form.html
    Success: redirect to grievance detail or list.
    """
    model = Grievance
    form_class = GrievanceForm
    template_name = 'citizen/grievance_form.html'

    def form_valid(self, form):
        # create category if needed
        cat = form.cleaned_data.get('category')
        cat_name = form.cleaned_data.get('category_name')
        if cat is None and cat_name:
            cat, _ = Category.objects.get_or_create(name=cat_name)
        # save grievance with logged-in user
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.category = cat
        self.object.save()
        messages.success(self.request, "Grievance submitted successfully.")
        return redirect('citizen:grievance-detail', pk=self.object.pk)

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the errors below.")
        return super().form_invalid(form)


class GrievanceDetailView(LoginRequiredMixin, DetailView):
    """
    Detail view for a grievance. Owners or officers/admin can view.
    Template: templates/citizen/grievance_detail.html
    """
    model = Grievance
    template_name = 'citizen/grievance_detail.html'
    context_object_name = 'grievance'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        user = request.user
        # owner can view, officer/admin can view
        if obj.user == user or user.is_staff or user.is_superuser or getattr(user, 'role', None) in ('officer', 'admin'):
            return super().dispatch(request, *args, **kwargs)
        messages.error(request, "You do not have permission to view this grievance.")
        return redirect('citizen:dashboard')

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.select_related('grievance','user').all()
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # citizens see only their feedbacks; officers/admin can see all
        if user.is_staff or user.is_superuser or getattr(user, 'role', None) in ('officer','admin'):
            return Feedback.objects.all()
        return Feedback.objects.filter(user=user)
