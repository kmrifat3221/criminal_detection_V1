from django import forms
from .models import Camera

class CameraForm(forms.ModelForm):
    CAMERA_TYPES = [
        ('builtin', 'Built-in Webcam'),
        ('usb', 'USB Camera'),
        ('ip', 'IP Camera'),
        ('mobile', 'Mobile Phone Camera'),
        ('rtsp', 'RTSP Stream (CCTV)'),
    ]
    
    camera_type = forms.ChoiceField(choices=CAMERA_TYPES)
    camera_url = forms.CharField(
        required=False,
        help_text='For IP cameras, mobile phones, or RTSP streams, enter the URL (e.g., http://192.168.1.100:8080/video or rtsp://...)'
    )
    camera_number = forms.IntegerField(
        required=False,
        min_value=0,
        help_text='For built-in or USB cameras, enter the camera number (0 for built-in, 1 or higher for USB)'
    )

    class Meta:
        model = Camera
        fields = ['location', 'description', 'is_active']

    def clean(self):
        cleaned_data = super().clean()
        camera_type = cleaned_data.get('camera_type')
        camera_url = cleaned_data.get('camera_url')
        camera_number = cleaned_data.get('camera_number')

        # Generate the camera_id based on type
        if camera_type in ['ip', 'mobile', 'rtsp']:
            if not camera_url:
                raise forms.ValidationError({
                    'camera_url': 'URL is required for IP cameras, mobile phones, and RTSP streams'
                })
            camera_id = camera_url.strip()  # Remove any whitespace
            if not camera_id:
                raise forms.ValidationError({
                    'camera_url': 'Camera URL cannot be empty'
                })
        elif camera_type in ['builtin', 'usb']:
            if camera_number is None:
                raise forms.ValidationError({
                    'camera_number': 'Camera number is required for built-in and USB cameras'
                })
            camera_id = str(camera_number)

        # Check if a camera with this ID already exists
        if Camera.objects.filter(camera_id=camera_id).exists():
            if camera_type in ['ip', 'mobile', 'rtsp']:
                raise forms.ValidationError({
                    'camera_url': f'A camera with URL "{camera_id}" already exists. Please use a different camera URL.'
                })
            else:
                raise forms.ValidationError({
                    'camera_number': f'A camera with number {camera_id} already exists. Please use a different camera number.'
                })

        # Ensure camera_id is set
        cleaned_data['camera_id'] = camera_id
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Ensure camera_id is set from cleaned_data
        instance.camera_id = self.cleaned_data['camera_id']
        if commit:
            instance.save()
        return instance
