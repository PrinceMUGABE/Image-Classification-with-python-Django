from django.conf import settings
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from . models import UserProfile
from .forms import ImageUploadForm, PhotoUploadForm, UserProfileForm
import cv2
import numpy as np
from PIL import Image
import imagehash
import os
from django.core.files.storage import default_storage
from PIL import Image
from django.utils.timezone import now, timedelta
from .models import  Activity
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from tensorflow.keras.applications.resnet50 import preprocess_input, decode_predictions
from tensorflow.keras.applications import ResNet50
from . import views
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from openpyxl import Workbook
import openpyxl
from django.utils.timezone import make_naive
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator






# Create your views here.

def home(request):
    return render(request, "authentication/index.html")


def signup(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            pass1 = form.cleaned_data['pass1']
            pass2 = form.cleaned_data['pass2']

            if pass1 == pass2:
                if User.objects.filter(username=username).exists():
                    messages.error(request, 'Username already exists')
                else:
                    myuser = User.objects.create_user(username=username, email=email, password=pass1)

                    user_profile = UserProfile.objects.create(user=myuser)

                    activity = Activity.objects.create(user=myuser, action='User signed up')

                    myuser.save()

                    messages.success(request, 'Registered successfully')
                    return redirect('signin')  # Redirect to signin (login) page after successful signup

            else:

                messages.error(request, 'Password mismatch')
        else:
            messages.error(request, 'Invalid form data. Please check the fields.')
    else:
        form = UserProfileForm()

    return render(request, 'authentication/signup.html', {'form': form})

def compare_images(image1, image2):
    hash1 = imagehash.average_hash(image1)
    hash2 = imagehash.average_hash(image2)

    threshold = 10
    if hash1 - hash2 < threshold:
        return True  # Images are similar
    else:
        return False  # Images are different


def dashboard(request):
    user = request.user
    user_profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        image_form = ImageUploadForm(request.POST, request.FILES)
        if image_form.is_valid():
            uploaded_image = request.FILES['image']

            is_similar = compare_images(
                Image.open(user_profile.profile_picture.path),
                Image.open(uploaded_image)
            )

            if is_similar:
                messages.success(request, 'No cheating detected!')
            else:
                messages.error(request, 'Cheating detected!')
    else:
        image_form = ImageUploadForm()
        print('Image not uploaded')

    context = {'username': user.username, 'image_form': image_form}
    return render(request, "authentication/dashboard.html", context)





@login_required()
def signout(request):
    # user = get_object_or_404(User, id=user_id)
    # # Log the "User deleted" activity
    # Activity.objects.create(user=request.user, action=f'User deleted: {user.username}')
    return render(request, "authentication/signin.html")





def dashboard_admin(request):
    username = request.user.username
    # calculate total users
    total_users = User.objects.all().count()
    users = User.objects.all()

    # Calculate the date threshold for considering users as active (e.g., logged in within the last 7 days)
    active_threshold = now() - timedelta(days=7)
    # Count the number of active users
    active_users = User.objects.filter(last_login__gte=active_threshold).count()

    # calculate new users of today
    # Calculate the start and end of today
    today_start = now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now().replace(hour=23, minute=59, second=59, microsecond=999999)

    # Count the number of new users registered today
    new_users_today = User.objects.filter(date_joined__range=(today_start, today_end)).count()

    # Retrieve the latest activity data
    latest_activity = Activity.objects.order_by('-timestamp')[:5]

    context = {'username': username,
               'users': users,

               'total_users': total_users,
               'active_users': active_users,
               'new_users_today':new_users_today,
               'latest_activities': latest_activity}

    return render(request, "authentication/dashboard_admin.html", context)



from django.contrib.auth.models import User
from django.urls import reverse

# ...

@login_required
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        # Get the submitted data from the form
        new_username = request.POST.get('username')
        new_email = request.POST.get('email')

        # Validate and update the user's data
        if new_username and new_email:
            user.username = new_username
            user.email = new_email
            user.save()

            # Log the "User edited" activity
            Activity.objects.create(user=request.user, action=f'User edited: {user.username}')
            messages.success(request, f'User {user} edited successfully')
            # Redirect to the "Manage Users" form
            return redirect(reverse('manage_users_form'))

        else:
            messages.error(request, 'Edit {user} failed')
            return JsonResponse({'success': False, 'message': 'Invalid data. Both username and email are required.'})

    return render(request, 'authentication/edit_user.html', {'user': user})


@login_required
def delete_user(request, user_id):
    try:
        user = get_object_or_404(User, id=user_id)

        if request.method == 'POST':
            # Log the "User deleted" activity
            Activity.objects.create(user=request.user, action=f'User deleted: {user.username}')

            # Delete the user
            user.delete()

            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'message': 'Invalid request method.'})

    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Failed to delete user: {str(e)}'})

def about(request):
    return render(request, 'authentication/about.html')


def analyze_image(image):
    # Load the ResNet50 model (pre-trained on ImageNet)
    model = ResNet50(weights='imagenet')

    # Load and preprocess the uploaded image
    img = Image.open(image)
    img = img.resize((224, 224))
    img_array = np.array(img)
    img_array = preprocess_input(np.expand_dims(img_array, axis=0))

    # Make predictions using the model
    predictions = model.predict(img_array)
    decoded_predictions = decode_predictions(predictions, top=3)[0]

    return decoded_predictions


@never_cache
def manage_users_form(request):

    global selected_user, latest_activities
    username = request.user.username
    # calculate total users
    total_users = User.objects.all().count()
    users = User.objects.all()

    # Calculate the date threshold for considering users as active (e.g., logged in within the last 7 days)
    active_threshold = now() - timedelta(days=7)
    # Count the number of active users
    active_users = User.objects.filter(last_login__gte=active_threshold).count()

    # calculate new users of today
    # Calculate the start and end of today
    today_start = now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now().replace(hour=23, minute=59, second=59, microsecond=999999)

    # Count the number of new users registered today
    new_users_today = User.objects.filter(date_joined__range=(today_start, today_end)).count()

    # Retrieve the latest activity data
    all_activities = Activity.objects.all().order_by('-timestamp')

    # Create a Paginator object with the activities and specify the number of items per page (e.g., 10)
    paginator = Paginator(all_activities, 10)  # Change '10' to the desired number of activities per page

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the Page object for the current page
    page = paginator.get_page(page_number)


    for user in users:
        print(user.id)

        # Initialize variables for filtering
        selected_user = None
        latest_activities = Activity.objects.all()

        # Check if a username is provided in the GET request
    search_username = request.GET.get('username')

    if search_username:
        # If a username is provided, try to get the user and filter activities
        selected_user = get_object_or_404(User, username=search_username)
        latest_activities = Activity.objects.filter(user=selected_user).order_by('-timestamp')
    else:
        # If no username is provided, retrieve all activities
        latest_activities = Activity.objects.all().order_by('-timestamp')

    context = {
        'username': username,
        'users': users,
        'total_users': total_users,
        'selected_user': selected_user,
        'active_users': active_users,
        'latest_activities': latest_activities,
        'new_users_today': new_users_today,
        'all_activities': all_activities}

    return render(request, 'authentication/manage_users_form.html',context)


def compare_images_content(uploaded_image, existing_image_paths):
    uploaded_image_hash = imagehash.average_hash(uploaded_image)

    for existing_image_path in existing_image_paths:
        existing_image = Image.open(existing_image_path)
        existing_image_hash = imagehash.average_hash(existing_image)

        # Compare the average hashes
        hash_difference_threshold = 10
        if abs(uploaded_image_hash - existing_image_hash) < hash_difference_threshold:
            return True  # Images have similar content

    return False  # No similar image found

def upload_photo(request):
    if request.method == 'POST':
        form = PhotoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_photo = form.cleaned_data['photo']

            # Path to the directory containing existing images
            existing_images_dir = os.path.join(settings.MEDIA_ROOT, 'uploaded_photos')

            existing_image_paths = [
                os.path.join(existing_images_dir, filename)
                for filename in os.listdir(existing_images_dir)
            ]

            uploaded_image = Image.open(uploaded_photo)

            # Compare the uploaded image with existing images based on content
            is_similar = compare_images_content(uploaded_image, existing_image_paths)

            if is_similar:
                messages.success(request, 'No cheating detected!')
            else:
                messages.error(request, 'Cheating detected!')

        else:
            messages.error(request, 'Invalid form data. Please check the field.')

    else:
        form = PhotoUploadForm()

    return render(request, 'authentication/photo_upload.html', {'form': form})


def generate_excel(request):
    type = request.GET.get('type')
    ids = request.GET.get('ids')
    search_username = request.GET.get('search_username', '')

    if search_username:
        activities = Activity.objects.filter(id__in=ids.split(','), user__username__icontains=search_username)
    else:
        activities = Activity.objects.filter(id__in=ids.split(','))

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=activity_data.xlsx'

    wb = Workbook()
    ws = wb.active

    if type == 'activity-data':
        # Write headers
        ws.append(['USERNAME', 'ACTIVITY', 'DATE & TIME'])

        for activity in activities:
            # Extract attributes and write data
            user = activity.user.username
            action = activity.action
            timestamp = make_naive(activity.timestamp)  # Convert to naive datetime
            ws.append([user, action, timestamp])

    wb.save(response)
    return response



@login_required
def make_user_admin(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = get_object_or_404(User, id=user_id)

        if not user.is_staff:  # Check if the user is not already an admin
            user.is_staff = True
            user.save()
            print(f'User "{user.username}" is now an admin.')  # Print success message to console
            return JsonResponse({'success': True, 'is_admin': True})
        else:
            print(f'User "{user.username}" is already an admin.')  # Print warning message to console
            return JsonResponse({'success': True, 'is_admin': True})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


@login_required
def signin(request):
    if request.method == "POST":
        username = request.POST.get('username').strip()
        password = request.POST.get('pass1')

        # Authenticate the user
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)

            # Check if the user is an admin
            if user.is_staff:
                # Redirect admin user to dashboard_admin
                return redirect('dashboard_admin')
            else:
                # Redirect regular user to dashboard
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')

    return render(request, 'authentication/signin.html')





@login_required
def generate_pdf(request):
    selected_ids = request.GET.get('ids', '').split(',')
    search_username = request.GET.get('search_username', '')

    if search_username:

        activities = Activity.objects.filter(id__in=selected_ids, user__username__icontains=search_username)
    else:
        activities = Activity.objects.filter(id__in=selected_ids)

    # Create a response object
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="activity_report.pdf"'

    # Create a PDF document
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []

    # Define the data for the table
    data = [['USERNAME', 'ACTIVITY', 'DATE & TIME']]

    for activity in activities:
        user = activity.user.username
        action = activity.action
        timestamp = str(activity.timestamp)
        data.append([user, action, timestamp])

    # Create the table and set its style
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), (0.7, 0.7, 0.7)),
        ('TEXTCOLOR', (0, 0), (-1, 0), (1, 1, 1)),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), (0.9, 0.9, 0.9)),
        ('GRID', (0, 0), (-1, -1), 0.5, (0.7, 0.7, 0.7)),
    ]))

    elements.append(table)

    # Build the PDF document
    doc.build(elements)

    return response


import json
from django.views.decorators.http import require_POST

@require_POST  # Ensure that this view only responds to POST requests
def delete_selected_activities(request):
    try:
        # Retrieve the selected activity IDs from the POST data
        data = json.loads(request.body)
        selected_ids = data.get('ids', [])

        # Perform the deletion logic here, assuming you have a model named 'Activity'
        from .models import Activity  # Import your Activity model
        Activity.objects.filter(id__in=selected_ids).delete()

        # Return a success response
        return JsonResponse({'success': True})
    except Exception as e:
        # Log any exceptions for debugging
        print('Error:', str(e))
        return JsonResponse({'success': False, 'error': str(e)})







from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import Activity

def get_user_activities(request):
    if request.method == "GET":
        search_username = request.GET.get("username")

        if search_username:
            # Get the user with the specified username
            user = User.objects.filter(username=search_username).first()

            if user:
                # Fetch activities for the selected user
                activities = Activity.objects.filter(user=user)

                # Render the activities as HTML
                latest_activities_html = render_to_string(
                    "authentication/latest_activities_table.html",
                    {"activities": activities},
                )

                return JsonResponse(
                    {"success": True, "latestActivitiesHtml": latest_activities_html}
                )

    return JsonResponse({"success": False})
