from app.models.user import User
from app.models.course import Course
from app.models.teacher import Teacher
from app.models.student import Student
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.grade import Grade
from app.models.news import News
from app.models.testimonial import Testimonial
from app.models.certificate import Certificate
from app.models.contact import Contact
from app.models.settings import SiteSettings

__all__ = [
    'User', 'Course', 'Teacher', 'Student', 'Enrollment',
    'Lesson', 'Grade', 'News', 'Testimonial', 'Certificate',
    'Contact', 'SiteSettings'
]
