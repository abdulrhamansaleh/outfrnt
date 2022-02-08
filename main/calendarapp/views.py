from django.views.generic import ListView
from calendarapp.models import Event,Archived
from calendarapp.utils import Calendar
from calendarapp.forms import EventForm,outfrntEventForm
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.views import generic
from django.utils.safestring import mark_safe
from datetime import timedelta, datetime, date
import calendar
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from accounts.views import home
from accounts.models import User

@login_required(login_url = '/signin/')
def all_events_view(request):
    if request.user.is_client:
        return render(request, 'calendarapp/events_list.html' , {"events": Event.objects.get_all_events(user = request.user)})
    else:
        return home(request)

@login_required(login_url = '/signin/')
def current_events_view(request):
    if request.user.is_client:
        return render(request, 'calendarapp/events_list.html' , {"events": Event.objects.get_running_events(user = request.user)})
    else:
        return home(request)

def get_date(req_day):
    if req_day:
        year, month = (int(x) for x in req_day.split('-'))
        return date(year, month, day=1)
    return datetime.today()

def prev_month(d):
    first = d.replace(day=1)
    prev_month = first - timedelta(days=1)
    month = 'month=' + str(prev_month.year) + '-' + str(prev_month.month)
    return month

def next_month(d):
    days_in_month = calendar.monthrange(d.year, d.month)[1]
    last = d.replace(day=days_in_month)
    next_month = last + timedelta(days=1)
    month = 'month=' + str(next_month.year) + '-' + str(next_month.month)
    return month

# View for client calendars 
class CalendarViewNew(LoginRequiredMixin,generic.View):
    # View variables 
    login_url = 'accounts:signin'
    template_name = 'calendar.html'

    # retrieve calendar data to display for clients 
    def get(self, request):
        # check if user logged is of client permissions 
        if request.user.is_client:
            forms = EventForm
            events = Event.objects.get_all_events(user = request.user)
            events_month = Event.objects.get_running_events(user = request.user)
            event_list = []
            for event in events:
                event_list.append({
                    'title': event.title,
                    'start': event.start_time.date().strftime("%Y-%m-%dT%H:%M:%S"),
                    'end': event.end_time.date().strftime("%Y-%m-%dT%H:%M:%S"),
                })
            variables = {
                'form': forms,
                'events': event_list,
                'events_month': events_month
            }
            return render(request,'calendarapp/calendar.html', variables)
        # return unauthenticaed users to home page 
        else:
            return home(request)

    # post the add task method form info 
    def post(self, request):
        # check if user is authenticated for form post and client view 
        if request.user.is_client:
            forms = EventForm(request.POST)
            if forms.is_valid():
                form = forms.save(commit=False)
                form.user = request.user
                form.save()
                return redirect('calendarapp:calendar')
            variables = {
                'form': forms
            }
            return render(request, 'calendarapp/calendar.html', variables)
        # return unauthenticated users to home page 
        else:
            return home(request)


# built-in decorator to check if user is logged in  
@login_required(login_url = '/signin/')
# add outfrnt tasks for clients 
def outfrnt_tasks(request):
    # check if user logged is of coach permission
    if request.user.is_coach:
        # needed queries 
        task = Event.objects.filter(outfrnt_task = True)
        clients = User.objects.all()
        # form to add task 
        form = outfrntEventForm(request.POST or None)
        if request.POST and form.is_valid():
            user = form.cleaned_data['user']
            title = form.cleaned_data['title']
            description = form.cleaned_data['description']
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']

            task = Event.objects.get_or_create(
                user = user,
                title = title,
                description = description,
                start_time = start_time,
                end_time = end_time,
                outfrnt_task = True  
            )

            # clear form 
            form = outfrntEventForm
            variables = {
            'form':form,
            'tasks':task,
            }
            return redirect('calendarapp:outfrnt_task')

        if 'search-key' in request.GET:
            search = request.GET['search-key']
            client = User.objects.filter(username = search)
            tasks = Event.objects.filter(outfrnt_task = True, user__in = client) 
            variables = {
                    'users':client ,
                    'tasks':tasks ,
                    'form':form
            }
            return render(request,'coach/outfrntTasks.html',variables)
        return render(request,'coach/outfrntTasks.html',{'users':clients , 'tasks':task , 'form':form})
    # return user to home page if not authenticated with permission to view  
    else:
        return home(request)

@login_required(login_url = '/signin/')
def delete_outfrnt_task(request,event_id):
    if request.user.is_coach:
        Event.objects.get(id = event_id).delete()
        return HttpResponseRedirect(reverse('calendarapp:outfrnt_task'))
    else:
         return home(request)
       
       
# built-in decorator to check if user is logged in  
@login_required(login_url = '/signin/')
def delete_task(request,event_id):
    # check if user logged is of client permissions 
    if request.user.is_client:
        # query event to be deleted based on id
        event_to_archive = Event.objects.get(id = event_id)
        Archived.objects.get_or_create(
                user = request.user,
                title = event_to_archive.title,
                description = event_to_archive.description,
                start_time = event_to_archive.start_time,
                end_time = event_to_archive.end_time
        )
        # remove event from all user views 
        event_to_archive.delete()
        return redirect('dashboard')
    else:
        return home(request)

# render a detail task view for coaches and clients 
@login_required(login_url = '/signin/')
def detail_task_view(request,event_id):
    user = request.user
    # query the task 
    task = Event.objects.get(id = event_id)
    print (task.user)
    print(user.is_client)
    # check if coach is trying to access view 
    if user.is_coach :
        # render the task through the context 
        variables = {
                "task":task
        }
        return render(request,'calendarapp/detail_view.html',variables)
    # check if client is trying to access view 
    if user.is_client and task.user == user:
        # render the task through the context 
        variables = {
                "task":task
        }
        return render(request,'calendarapp/detail_view_client.html',variables) 
    else:
        return home(request)


        
    
