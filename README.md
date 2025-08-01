# Real-Time Face Recognition and Criminal Detection System
Built with Django, this system offers real-time face recognition and criminal identification using CCTV camera feeds.

## Features
- Real-time face detection and recognition
- Criminal database integration
- High accuracy detection using machine learning
- Automatic alert system
- Live CCTV feed processing

## Installation

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Apply migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

DEBUG=True
```

## Usage
1. Access the admin panel at `/admin`
2. Add criminal records with photos
3. Start the real-time detection system
4. Monitor alerts through the dashboard

## Security Note
This system handles sensitive data. Ensure proper security measures are in place before deployment.

## Admin login
1. username: Rifat
2. Email: kmrifat3221@gmail.com
3. Password: 1234


