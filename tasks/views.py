from venv import logger
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect, render, get_object_or_404, get_list_or_404
from django.views import View
from django.views.generic.edit import FormView, UpdateView
from django.urls import reverse
from matplotlib.ticker import MaxNLocator
from tasks.forms import LogInForm, PasswordForm, UserForm, SignUpForm, JournalEntryForm, UserPreferenceForm
from tasks.models import JournalEntry, UserPreferences, User
from tasks.helpers import login_prohibited
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from collections import Counter
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from django.http import HttpResponse
from reportlab.lib.enums import TA_CENTER


DEFAULT_TEMPLATE = {"name" : "Default template", "text" : "This is the default template"}

@login_required
def dashboard(request):
    return render(request, 'dashboard.html', {'user': request.user})

@login_required
def journal_log(request):
    return render(request, 'journal_log.html', {'journal_entries' : JournalEntry.objects.filter(user=request.user)})

@login_required
def templates(request):
    return render(request, 'templates.html', {"templates": [DEFAULT_TEMPLATE]})

@login_required
def trash(request):
    return render(request, 'trash.html',{'journal_entries' : JournalEntry.objects.filter(user=request.user)})

@login_required
def mood_breakdown(request):
    return render(request, 'mood_breakdown.html')


@login_prohibited
def home(request):
    """Display the application's start/home screen."""

    return render(request, 'home.html')

def export_journal_entry_to_pdf(request, entry_id):
    journal_entry = get_object_or_404(JournalEntry, pk=entry_id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{journal_entry.title}.pdf"'

    p = canvas.Canvas(response)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(72, 800, journal_entry.title) 

    p.setFont("Helvetica", 12)
    text_object = p.beginText(72, 780)  
    text_object.setLeading(15)  

    for line in journal_entry.text.split('\n'):  
        text_object.textLine(line)
   
    p.drawText(text_object)

    p.showPage()
    p.save()
    return response

def export_journal_entry_to_rtf(request, entry_id):
    journal_entry = get_object_or_404(JournalEntry, pk=entry_id)
    response = HttpResponse(content_type='application/rtf')
    response['Content-Disposition'] = f'attachment; filename="{journal_entry.title}.rtf"'
    rtf_content = "{\\rtf1\\ansi\\deff0 "
    rtf_content += "{\\b " + journal_entry.title + "}"
    rtf_content += "\\line "
    rtf_content += journal_entry.text.replace('\n', '\\line ')
    rtf_content += " }"

    response.write(rtf_content)
    return response

def get_pdf_elements_for_entry(entry, styles):
    elements = []
    title_style = ParagraphStyle(name='title_style', parent=styles['Title'], alignment=TA_CENTER)
    
   
    elements.append(Paragraph(entry.title, title_style))
    elements.append(Spacer(1, 12))
    

    content_style = styles['BodyText']
    elements.append(Paragraph(entry.text, content_style))
    elements.append(PageBreak())  

    return elements
def get_rtf_content_for_entry(entry):
    rtf_content = []
    rtf_content.append(r"{\pard\qc\b " + entry.title + r"\b0\par}")  
    rtf_content.append(r"{\pard " + entry.text.replace("\n", r"\par ") + r"\par}") 
    rtf_content.append(r"\page") 
    return "\n".join(rtf_content)

def export_entries(request):
    entry_ids = request.GET.get('entries', '').split(',')
    entry_ids = [int(id) for id in entry_ids if id.isdigit()]
    export_format = request.GET.get('format', 'pdf')

    entries = get_list_or_404(JournalEntry, id__in=entry_ids)

    if export_format == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="journal_entries.pdf"'
        
        doc = SimpleDocTemplate(response, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        for entry in entries:
            elements += get_pdf_elements_for_entry(entry, styles)
        
        doc.build(elements)
        return response

    elif export_format == 'rtf':
        response = HttpResponse(content_type='application/rtf')
        response['Content-Disposition'] = 'attachment; filename="journal_entries.rtf"'
        
        rtf_content = []
        rtf_content.append(r"{\rtf1\ansi")  
        for entry in entries:
            rtf_content.append(get_rtf_content_for_entry(entry))
        rtf_content.append("}")  

        response.write("\n".join(rtf_content))
        return response

    else:
        return HttpResponse("Unsupported format", status=400)
class LoginProhibitedMixin:
    """Mixin that redirects when a user is logged in."""

    redirect_when_logged_in_url = None

    def dispatch(self, *args, **kwargs):
        """Redirect when logged in, or dispatch as normal otherwise."""
        if self.request.user.is_authenticated:
            return self.handle_already_logged_in(*args, **kwargs)
        return super().dispatch(*args, **kwargs)

    def handle_already_logged_in(self, *args, **kwargs):
        url = self.get_redirect_when_logged_in_url()
        return redirect(url)

    def get_redirect_when_logged_in_url(self):
        """Returns the url to redirect to when not logged in."""
        if self.redirect_when_logged_in_url is None:
            raise ImproperlyConfigured(
                "LoginProhibitedMixin requires either a value for "
                "'redirect_when_logged_in_url', or an implementation for "
                "'get_redirect_when_logged_in_url()'."
            )
        else:
            return self.redirect_when_logged_in_url


class LogInView(LoginProhibitedMixin, View):
    """Display login screen and handle user login."""

    http_method_names = ['get', 'post']
    redirect_when_logged_in_url = settings.REDIRECT_URL_WHEN_LOGGED_IN

    def get(self, request):
        """Display log in template."""

        self.next = request.GET.get('next') or ''
        return self.render()

    def post(self, request):
        """Handle log in attempt."""

        form = LogInForm(request.POST)
        self.next = request.POST.get('next') or settings.REDIRECT_URL_WHEN_LOGGED_IN
        user = form.get_user()
        if user is not None:
            login(request, user)
            return redirect(self.next)
        messages.add_message(request, messages.ERROR, "The credentials provided were invalid!")
        return self.render()

    def render(self):
        """Render log in template with blank log in form."""

        form = LogInForm()
        return render(self.request, 'log_in.html', {'form': form, 'next': self.next})


def log_out(request):
    """Log out the current user"""

    logout(request)
    return redirect('home')


class PasswordView(LoginRequiredMixin, FormView):
    """Display password change screen and handle password change requests."""

    template_name = 'password.html'
    form_class = PasswordForm

    def get_form_kwargs(self, **kwargs):
        """Pass the current user to the password change form."""

        kwargs = super().get_form_kwargs(**kwargs)
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        """Handle valid form by saving the new password."""

        form.save()
        login(self.request, self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect the user after successful password change."""

        messages.add_message(self.request, messages.SUCCESS, "Password updated!")
        return reverse('dashboard')


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Display user profile editing screen, and handle profile modifications."""

    model = UserForm
    template_name = "profile.html"
    form_class = UserForm

    def get_object(self):
        """Return the object (user) to be updated."""
        user = self.request.user
        return user

    def get_success_url(self):
        """Return redirect URL after successful update."""
        messages.add_message(self.request, messages.SUCCESS, "Profile updated!")
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)


class SignUpView(LoginProhibitedMixin, FormView):
    """Display the sign up screen and handle sign ups."""

    form_class = SignUpForm
    template_name = "sign_up.html"
    redirect_when_logged_in_url = settings.REDIRECT_URL_WHEN_LOGGED_IN
    

    def form_valid(self, form):
        self.object = form.save()
        login(self.request, self.object)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("set_preferences")
    
   


class CreateJournalEntryView(LoginRequiredMixin, FormView):
    """Display the create entry screen and handle entry creation"""

    form_class = JournalEntryForm
    template_name = "create_entry.html"
    model = JournalEntryForm

    def get_form_kwargs(self, **kwargs):
        """Pass the current user to the create entry form."""

        kwargs = super().get_form_kwargs(**kwargs)
        kwargs.update({'user': self.request.user, 'text': DEFAULT_TEMPLATE["text"]})
        return kwargs


    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
    

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Created new entry!")
        return reverse('journal_log')

def delete_journal_entry(request,entry_id):
    entry = JournalEntry.objects.get(pk=entry_id)
    if entry.user == request.user:
        entry.delete_entry()
        messages.add_message(request, messages.SUCCESS, "Entry moved to trash!")
        return redirect('trash')
    else:
        messages.add_message(request, messages.ERROR, "You cannot delete an entry that is not yours!")
        return redirect('journal_log')
    
def recover_journal_entry(request,entry_id):
    entry = JournalEntry.objects.get(pk=entry_id)
    if entry.user == request.user:
        entry.recover_entry()
        messages.add_message(request,messages.SUCCESS,"Entry has been recovered!")
        return redirect('journal_log')
    else:
        messages.add_message(request, messages.ERROR, "entry cannot be recovered")
        return redirect('journal_log')

def delete_journal_entry_permanent(request,entry_id):
    entry = JournalEntry.objects.get(pk=entry_id)
    if entry.user == request.user:
        entry.delete()
        messages.add_message(request, messages.SUCCESS, "Entry deleted!")
        return redirect("journal_log") 
    else:
        messages.add_message(request, messages.ERROR, "You cannot delete an entry that is not yours!")
        return redirect('journal_log')


def get_mood_representation(mood, use_emoji=False):
    mood_dict = {
        1: ('Very Sad', '😔'),
        2: ('Sad', '🙁'),
        3: ('Neutral', '😐'),
        4: ('Happy', '🙂'),
        5: ('Very Happy', '😄')
    }
    description, emoji = mood_dict.get(mood, ('', ''))
    return f"{description} {emoji}" if use_emoji else description


def generate_mood_chart(user):
    one_month_ago = timezone.now() - timedelta(days=30)
    entries = JournalEntry.objects.filter(user=user, created_at__gte=one_month_ago, deleted=False)
    moods = entries.values_list('mood', flat=True)
    mood_counts = Counter(moods)

    mood_labels = [get_mood_representation(mood) for mood in mood_counts.keys()]
    counts = list(mood_counts.values())

    fig, ax = plt.subplots()
    ax.bar(mood_labels, counts)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    for i, count in enumerate(counts):
        ax.text(i, count + 0.1, str(count), ha='center')

    flike = BytesIO()
    plt.savefig(flike, format='png', bbox_inches='tight')
    plt.close(fig)
    b64 = base64.b64encode(flike.getvalue()).decode()

    return b64

@login_required
def mood_breakdown(request):
    today = timezone.now()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    user_entries = JournalEntry.objects.filter(user=request.user, deleted=False)

    # Aggregating mood data for today, this week, and this month
    mood_today = user_entries.filter(created_at__date=today.date()).values('mood').annotate(count=Count('mood')).order_by('-count').first()
    mood_week = user_entries.filter(created_at__gte=start_of_week).values('mood').annotate(count=Count('mood')).order_by('-count').first()
    mood_month = user_entries.filter(created_at__gte=start_of_month).values('mood').annotate(count=Count('mood')).order_by('-count').first()

    # Convert mood numbers to emojis for display
    # Convert mood numbers to emojis for display
    mood_today_average = get_mood_representation(mood_today['mood'], use_emoji=True) if mood_today else 'No entries today'
    mood_week_average = get_mood_representation(mood_week['mood'], use_emoji=True) if mood_week else 'No entries this week'
    mood_month_average = get_mood_representation(mood_month['mood'], use_emoji=True) if mood_month else 'No entries this month'

    # Generate mood chart for the past month
    mood_chart = generate_mood_chart(request.user)

    context = {
        'mood_today': mood_today_average,
        'mood_week':  mood_week_average,
        'mood_month': mood_month_average,
        'mood_chart': mood_chart,
    }

    return render(request, 'mood_breakdown.html', context)


class SetPreferences(LoginRequiredMixin, FormView):
    """Display the create entry screen and handle entry creation"""

    form_class = UserPreferenceForm
    template_name = "set_preferences.html"

    def dispatch(self, request, *args, **kwargs):
        """ If a preference form has already been made for the user they do not 
        need to access this page therefore it redirects"""
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if UserPreferences.objects.filter(user=request.user).exists():
            messages.warning(request, "Preferences already exist.")
            return redirect('dashboard')  

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user_preference = form.save(commit=False)
        user_preference.user = self.request.user
        user_preference.save()
        messages.success(self.request, "Preferences Saved!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('dashboard')
    
class EditPreferences(LoginRequiredMixin, UpdateView):
    """Display user profile editing screen, and handle profile modifications."""

    model = UserPreferences
    template_name = "edit_preferences.html"
    form_class = UserPreferenceForm

     
    def get_success_url(self):
        return reverse('dashboard')

    def get_object(self, queryset=None):
        """Return the object (user preferences) to be updated."""
        return get_object_or_404(UserPreferences, user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Preferences updated!")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)