# adminpanel/forms.py
from django import forms

class SettingsForm(forms.Form):
    """
    Admin panel settings form.
    Controls page-size, SLA days, and notification preferences.
    """

    default_page_size = forms.IntegerField(
        min_value=5,
        max_value=200,
        initial=25,
        label="Default page size",
        widget=forms.NumberInput(attrs={
            "class": "w-32 px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-sky-500",
            "placeholder": "25",
        })
    )

    sla_days = forms.IntegerField(
        min_value=0,
        max_value=365,
        initial=7,
        label="Default SLA (days)",
        widget=forms.NumberInput(attrs={
            "class": "w-32 px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-sky-500",
            "placeholder": "7",
        })
    )

    notifications_enabled = forms.BooleanField(
        required=False,
        initial=True,
        label="Enable Notifications",
        widget=forms.CheckboxInput(attrs={
            "class": "h-5 w-5 text-sky-600 border-gray-300 rounded focus:ring-sky-500",
        })
    )

    notification_email = forms.EmailField(
        required=False,
        label="Notification email (from)",
        widget=forms.EmailInput(attrs={
            "class": "w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-sky-500",
            "placeholder": "no-reply@example.com",
        })
    )

    def clean(self):
        """
        Ensure notification email is present when notifications_enabled is True.
        """
        cleaned_data = super().clean()
        enabled = cleaned_data.get("notifications_enabled")
        email = cleaned_data.get("notification_email")

        if enabled and not email:
            self.add_error(
                "notification_email",
                "Email is required if notifications are enabled."
            )

        return cleaned_data

