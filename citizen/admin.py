from django.contrib import admin
from .models import Category, Grievance, Feedback


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Grievance)
class GrievanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'citizen', 'category', 'title', 'status', 'created_at')
    list_filter = ('status', 'category',)
    search_fields = ('title', 'description', 'citizen__username')


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'grievance', 'rating', 'created_at')
    list_filter = ('rating',)

