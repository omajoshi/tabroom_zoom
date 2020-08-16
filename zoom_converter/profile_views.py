from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.decorators import login_required

def email_activation_helper(request): # not a view!!!
    user = request.user
    subject = "Tabroom/Zoom/Converter - Please verify your email"
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_token_generator.make_token(user)
    relative_link = reverse('zoom_converter:activate_email', kwargs={'uidb64': uidb64, 'token': token})
    link = request.build_absolute_uri(relative_link)
    message = render_to_string('registration/email_activation_email.html', {'link': link})
    send_mail(subject, message, EMAIL_HOST_USER, [user.email], html_message=message)

def tabroom_activation_helper(request): # not a view!!!
    user = request.user
    subject = "Tabroom/Zoom/Converter - Please verify your Tabroom email"
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = tabroom_token_generator.make_token(user)
    relative_link = reverse('zoom_converter:activate_tabroom', kwargs={'uidb64': uidb64, 'token': token})
    link = request.build_absolute_uri(relative_link)
    message = render_to_string('registration/tabroom_activation_email.html', {'link': link})
    send_mail(subject, message, EMAIL_HOST_USER, [user.tabroom_email], html_message=message)

def zoom_activation_helper(request): # not a view!!!
    user = request.user
    subject = "Tabroom/Zoom/Converter - Please verify your Zoom email"
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = zoom_token_generator.make_token(user)
    relative_link = reverse('zoom_converter:activate_zoom', kwargs={'uidb64': uidb64, 'token': token})
    link = request.build_absolute_uri(relative_link)
    message = render_to_string('registration/zoom_activation_email.html', {'link': link})
    send_mail(subject, message, EMAIL_HOST_USER, [user.zoom_email], html_message=message)


def register(request):
    if request.user.is_authenticated:
        return redirect(request.GET.get('next', 'zoom_converter:tournament_list'))
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            email_activation_helper(request)
            tabroom_activation_helper(request)
            zoom_activation_helper(request)
            # 'we sent you an three different emails'
            return redirect('zoom_converter:profile')
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/register.html", {'form': form})







@login_required
def awaiting_email_activation(request):
    if request.user.email_confirmed:
        return redirect('zoom_converter:tournament_list')
    return HttpResponse(f'Please click the link in your email to activate.  Or click <a href="{reverse("logout")}">here</a> to log out.  Or click <a href="{reverse("zoom_converter:activation_email")}">here</a> to resend the email.')

@login_required
def send_email_activation(request):
    email_activation_helper(request)
    return redirect('zoom_converter:profile')

def activate_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64)
        user = User.objects.get(pk=uid)
    except:
        user = None
    if email_token_generator.check_token(user, token):
        user.email_confirmed = True
        user.save()
        login(request, user)
        return redirect('zoom_converter:profile')
    else:
        return HttpResponse('invalid activation key')



@login_required
def awaiting_tabroom_activation(request):
    if request.user.tabroom_confirmed:
        return redirect('zoom_converter:tournament_list')
    return HttpResponse(f'Please click the link in your email to activate.  Or click <a href="{reverse("logout")}">here</a> to log out.  Or click <a href="{reverse("zoom_converter:activation_email")}">here</a> to resend the email.')

@login_required
def send_tabroom_activation(request):
    tabroom_activation_helper(request)
    return redirect('zoom_converter:profile')

def activate_tabroom(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64)
        user = User.objects.get(pk=uid)
    except:
        user = None
    if tabroom_token_generator.check_token(user, token):
        user.tabroom_confirmed = True
        user.save()
        login(request, user)
        return redirect('zoom_converter:profile')
    else:
        return HttpResponse('invalid activation key')



@login_required
def awaiting_zoom_activation(request):
    if request.user.zoom_confirmed:
        return redirect('zoom_converter:tournament_list')
    return HttpResponse(f'Please click the link in your email to activate.  Or click <a href="{reverse("logout")}">here</a> to log out.  Or click <a href="{reverse("zoom_converter:activation_email")}">here</a> to resend the email.')

@login_required
def send_zoom_activation(request):
    zoom_activation_helper(request)
    return redirect('zoom_converter:profile')

def activate_zoom(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64)
        user = User.objects.get(pk=uid)
    except:
        user = None
    if zoom_token_generator.check_token(user, token):
        user.zoom_confirmed = True
        user.save()
        login(request, user)
        return redirect('zoom_converter:profile')
    else:
        return HttpResponse('invalid activation key')

@login_required
def profile(request):
    user = request.user
    if request.method == 'POST':
        data = [user.email, user.email_confirmed, user.tabroom_email, user.tabroom_confirmed, user.zoom_email, user.zoom_confirmed]
        form1 = EmailActivationForm(request.POST, instance=user)
        form2 = TabroomActivationForm(request.POST, instance=user)
        form3 = ZoomActivationForm(request.POST, instance=user)
        # check for duplicate people
        if form1.is_valid():
            if 'email' not in form1.changed_data:
                user.email = data[0]
                user.email_confirmed = data[1]
            else:
                email_activation_helper(request)
        if form2.is_valid():
            if 'tabroom_email' not in form2.changed_data:
                user.tabroom_email = data[2]
                user.tabroom_confirmed = data[3]
            else:
                tabroom_activation_helper(request)
        if form3.is_valid():
            if 'zoom_email' not in form3.changed_data:
                user.zoom_email = data[4]
                user.zoom_confirmed = data[5]
            else:
                zoom_activation_helper(request)
        user.save()
        return redirect('zoom_converter:profile')
    else:
        form1 = EmailActivationForm(instance=user)
        form2 = TabroomActivationForm(instance=user)
        form3 = ZoomActivationForm(instance=user)
    return render(request, 'registration/profile.html', context={'form1': form1, 'form2': form2, 'form3': form3})

