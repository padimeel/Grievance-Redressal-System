# adminpanel/forms.py
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
