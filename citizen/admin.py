# backend/citizen/admin.py
from django.contrib import admin
from .models import CitizenProfile, Category, Grievance,Feedback

@admin.register(CitizenProfile)
class CitizenProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Grievance)
class GrievanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user', 'category', 'status', 'assigned_to', 'created_at')
    list_filter = ('status', 'category')
    search_fields = ('title', 'description', 'user__username')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'grievance', 'user', 'rating', 'created_at')
    search_fields = ('grievance__title', 'user__username', 'comments')

