# officer/views.py
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView

class OfficerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_staff or getattr(user, 'role', None) == 'officer')

class OfficerDashboardView(LoginRequiredMixin, OfficerRequiredMixin, TemplateView):
    template_name = 'officer/dashboard.html'
