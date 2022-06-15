from django.shortcuts import render
from django.http import HttpResponseRedirect
from .models import Course, Enrollment, Lesson, Question, Choice, Submission
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))


# Submit view to create exam submission record for a course enrollment
def submit(request, course_id):
    # First get user and course object
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    # Then get associated enrollment object created when the user enrolled in course
    enrollment = Enrollment.objects.get(user=user, course=course)
    # Create submission object referring to the enrollment
    submission = Submission.objects.create(enrollment=enrollment)
    # Collect the selected choices from the exam form
    selected_choices = extract_answers(request)
    # For submission object, add foreign key to each selected choice object
    for choice in selected_choices:
        submission.choices.add(choice)
    # Finally, redirect to show_exam_result with the submission id
    return redirect('onlinecourse:show_exam_result', course_id=course.id, submission_id=submission.id)


# A provided method to collect the selected choices 
# from the exam form from the request object
def extract_answers(request):
    submitted_anwsers = []
    for key in request.POST:
        if key.startswith('choice'):
            value = request.POST[key]
            choice_id = int(value)
            submitted_anwsers.append(choice_id)
    return submitted_anwsers


# Exam result view to check if learner passed exam and 
# show their question results and result for each question
def show_exam_result(request, course_id, submission_id):
    # Get course and submission based on provided ids
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)
    # From submission record, get ids of the selected choices
    selected_choices = submission.choices.all()
    selected_ids = []
    for choice in selected_choices:
        selected_ids.append(choice.id)
    # Calculate maximum possible points and actual points earned
    points_possible = 0
    points_earned = 0
    # For every question in this course
    course_questions = Question.objects.filter(course=course)
    for question in course_questions:
        answered_correctly = True
        correct_choices = Choice.objects.filter(question__id=question.id).filter(is_correct=True)
        # Make sure all correct answers were selected
        for choice in correct_choices:
            if choice.id not in selected_ids:
                answered_correctly = False
        # Make sure no incorrect answers were selected
        for choice_id in selected_ids:
            choice = get_object_or_404(Choice, pk=choice_id)
            if not choice.is_correct:
                particular_question = Question.objects.get(choice__id=choice.id)
                if particular_question.id == question.id:
                    answered_correctly = False
        # Award points accordingly
        points_possible += question.grade
        if answered_correctly:
            points_earned += question.grade
    # Calculate grade
    grade = points_earned / points_possible
    # Add course, selected_ids, and grade to context for rendering HTML page
    context = {}
    context['course'] = course
    context['selected_ids'] = selected_ids
    context['grade'] = grade
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)