from django import forms
from .models import JobApplication, Position

class JobApplicationAdminForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['position'].queryset = Position.objects.all()
        self.fields['position'].empty_label = "Select a position"
