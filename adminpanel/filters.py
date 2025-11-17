# adminpanel/filters.py

import django_filters
from django.db.models import Q
from adminpanel.models import Grievance, Category
from django.contrib.auth import get_user_model

User = get_user_model()

class GrievanceFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')

    category = django_filters.CharFilter(method='filter_category')

    assigned_officer = django_filters.NumberFilter(field_name='assigned_officer__id')

    user = django_filters.NumberFilter(field_name='user__id')

    date_from = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')

    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Grievance
        fields = ['status', 'category', 'assigned_officer', 'user']

    def filter_category(self, queryset, name, value):
        """Allow filtering category using category ID or name."""
        return queryset.filter(
            Q(category__id=value) | 
            Q(category__name__icontains=value)
        )

    def filter_search(self, queryset, name, value):
        """General text search across title, description, and user name."""
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(user__username__icontains=value) |
            Q(user__first_name__icontains=value) |
            Q(user__last_name__icontains=value)
        )

