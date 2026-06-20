from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

from hello_world.support.models import Complaint, ComplaintComment, SupportProfile


class SupportLoginForm(AuthenticationForm):
    pass


class SupportUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(choices=SupportProfile.ROLE_CHOICES)
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ["username", "email", "role", "password1", "password2"]

    def __init__(self, *args, allowed_roles=None, **kwargs):
        super().__init__(*args, **kwargs)
        if allowed_roles is not None:
            self.fields["role"].choices = [choice for choice in SupportProfile.ROLE_CHOICES if choice[0] in allowed_roles]

    def save(self, commit=True):
        user = super().save(commit=commit)
        role = self.cleaned_data["role"]
        SupportProfile.objects.get_or_create(user=user, defaults={"role": role})
        return user


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ["title", "description", "assigned_to"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].required = False
        self.fields["assigned_to"].queryset = User.objects.filter(support_profile__role=SupportProfile.ROLE_ENGINEER)
        if user is not None:
            profile = getattr(user, "support_profile", None)
            if profile is None or not (profile.is_owner or profile.is_manager):
                self.fields.pop("assigned_to")


class ComplaintCommentForm(forms.ModelForm):
    class Meta:
        model = ComplaintComment
        fields = ["text"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 3, "placeholder": "Add a comment..."}),
        }
