import asyncio
import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from telegram.constants import ParseMode

from app import create_app, db
from app.models import (
    User, Student, Teacher, Course, Lesson, Grade, News, 
    Enrollment, SiteSettings, BotSession, BotStatistics
)
from app.utils.helpers import damascus_now

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

flask_app = create_app()

LOGIN_PHONE, LOGIN_PASSWORD = range(2)

def get_or_create_session(telegram_id, username=None, first_name=None, last_name=None):
    with flask_app.app_context():
        session = BotSession.query.filter_by(telegram_id=telegram_id).first()
        if not session:
            session = BotSession(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            db.session.add(session)
            db.session.commit()
        else:
            session.last_activity = damascus_now()
            session.username = username
            session.first_name = first_name
            session.last_name = last_name
            db.session.commit()
        return session

def update_statistics(increment_received=True, increment_sent=False):
    with flask_app.app_context():
        today = damascus_now().date()
        stats = BotStatistics.query.filter_by(date=today).first()
        if not stats:
            stats = BotStatistics(
                date=today,
                messages_received=0,
                messages_sent=0,
                total_users=0,
                active_users_today=0
            )
            db.session.add(stats)
        
        if increment_received:
            stats.messages_received += 1
        if increment_sent:
            stats.messages_sent += 1
        
        stats.total_users = BotSession.query.count()
        stats.active_users_today = BotSession.query.filter(
            BotSession.last_activity >= datetime.combine(today, datetime.min.time())
        ).count()
        
        db.session.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    session = get_or_create_session(
        user.id,
        user.username,
        user.first_name,
        user.last_name
    )
    update_statistics()
    
    with flask_app.app_context():
        settings = SiteSettings.query.first()
        institute_name = settings.institute_name if settings else "معهد القاسم للعلوم واللغات"
    
    welcome_text = f"""
🌟 مرحباً بك في {institute_name} 🌟

أنا بوت المعهد الذكي، هنا لمساعدتك!

📚 ماذا يمكنني أن أفعل لك؟

🔐 إذا كنت طالباً أو معلماً، يمكنك تسجيل الدخول للوصول إلى:
   • دوراتك ودروسك
   • درجاتك وتقييماتك
   • إدارة حسابك

📰 يمكن للجميع:
   • عرض الدورات المتاحة
   • قراءة آخر الأخبار
   • التعرف على المعلمين
   • التواصل مع المعهد

استخدم القائمة أدناه أو الأوامر التالية:
/login - تسجيل الدخول
/courses - عرض الدورات
/news - آخر الأخبار
/teachers - المعلمون
/help - المساعدة
"""
    
    keyboard = [
        [KeyboardButton("🔐 تسجيل الدخول"), KeyboardButton("📚 الدورات")],
        [KeyboardButton("📰 الأخبار"), KeyboardButton("👨‍🏫 المعلمون")],
        [KeyboardButton("ℹ️ المساعدة"), KeyboardButton("📞 التواصل")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    update_statistics(increment_sent=True)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    update_statistics()
    help_text = """
📖 *دليل استخدام البوت*

*الأوامر المتاحة للجميع:*
/start - بدء المحادثة
/help - عرض المساعدة
/courses - عرض جميع الدورات
/news - آخر الأخبار
/teachers - قائمة المعلمين
/contact - التواصل مع المعهد

*بعد تسجيل الدخول:*
/login - تسجيل الدخول
/dashboard - لوحة التحكم الخاصة بك
/mycourses - دوراتي
/mylessons - دروسي
/mygrades - درجاتي
/logout - تسجيل الخروج

*للطلاب:*
• عرض الدورات المسجل بها
• الوصول إلى الدروس وتحميل الملفات
• مراجعة الدرجات والتقييمات

*للمعلمين:*
• إدارة الدروس
• عرض قائمة الطلاب
• إدخال الدرجات

💡 يمكنك أيضاً استخدام الأزرار أسفل الشاشة للتنقل السريع!
"""
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    update_statistics(increment_sent=True)

async def login_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    session = get_or_create_session(user.id, user.username, user.first_name, user.last_name)
    update_statistics()
    
    with flask_app.app_context():
        session = BotSession.query.filter_by(telegram_id=user.id).first()
        if session and session.is_authenticated:
            user_obj = User.query.get(session.user_id)
            await update.message.reply_text(
                f"أنت مسجل دخول بالفعل كـ {user_obj.name} ({user_obj.role})\n\n"
                "استخدم /logout لتسجيل الخروج أولاً."
            )
            update_statistics(increment_sent=True)
            return ConversationHandler.END
    
    await update.message.reply_text(
        "🔐 *تسجيل الدخول*\n\n"
        "📱 الرجاء إدخال رقم جوالك:\n"
        "(مثال: 0912345678)\n\n"
        "أو /cancel للإلغاء",
        parse_mode=ParseMode.MARKDOWN
    )
    update_statistics(increment_sent=True)
    return LOGIN_PHONE

async def login_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone = update.message.text.strip()
    context.user_data['login_phone'] = phone
    update_statistics()
    
    await update.message.reply_text(
        "🔑 الرجاء إدخال كلمة المرور:\n\n"
        "أو /cancel للإلغاء"
    )
    update_statistics(increment_sent=True)
    return LOGIN_PASSWORD

async def login_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    password = update.message.text
    phone = context.user_data.get('login_phone')
    user_tg = update.effective_user
    update_statistics()
    
    await update.message.delete()
    
    with flask_app.app_context():
        user = User.query.filter_by(phone_number=phone).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                await update.message.reply_text(
                    "❌ حسابك غير نشط. يرجى التواصل مع الإدارة."
                )
                update_statistics(increment_sent=True)
                return ConversationHandler.END
            
            session = BotSession.query.filter_by(telegram_id=user_tg.id).first()
            session.authenticate(user)
            
            role_emoji = {
                'admin': '👑',
                'assistant': '🛡️',
                'teacher': '👨‍🏫',
                'student': '👨‍🎓'
            }
            
            keyboard = [
                [KeyboardButton("📊 لوحة التحكم"), KeyboardButton("📚 دوراتي")],
                [KeyboardButton("📖 دروسي"), KeyboardButton("📝 درجاتي")],
                [KeyboardButton("📰 الأخبار"), KeyboardButton("🚪 تسجيل الخروج")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                f"✅ تم تسجيل الدخول بنجاح!\n\n"
                f"{role_emoji.get(user.role, '👤')} مرحباً {user.name}\n"
                f"📋 الدور: {user.role}\n\n"
                f"استخدم القائمة أدناه أو /dashboard للبدء",
                reply_markup=reply_markup
            )
            update_statistics(increment_sent=True)
        else:
            await update.message.reply_text(
                "❌ رقم الجوال أو كلمة المرور غير صحيحة.\n\n"
                "حاول مرة أخرى باستخدام /login"
            )
            update_statistics(increment_sent=True)
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    update_statistics()
    await update.message.reply_text(
        "تم إلغاء العملية ✅\n\nاستخدم /start للعودة إلى القائمة الرئيسية"
    )
    update_statistics(increment_sent=True)
    return ConversationHandler.END

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    update_statistics()
    
    with flask_app.app_context():
        session = BotSession.query.filter_by(telegram_id=user.id).first()
        if session and session.is_authenticated:
            session.logout()
            
            keyboard = [
                [KeyboardButton("🔐 تسجيل الدخول"), KeyboardButton("📚 الدورات")],
                [KeyboardButton("📰 الأخبار"), KeyboardButton("👨‍🏫 المعلمون")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                "👋 تم تسجيل الخروج بنجاح!\n\n"
                "يمكنك تسجيل الدخول مرة أخرى باستخدام /login",
                reply_markup=reply_markup
            )
            update_statistics(increment_sent=True)
        else:
            await update.message.reply_text("أنت لست مسجل دخول!")
            update_statistics(increment_sent=True)

async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    update_statistics()
    
    with flask_app.app_context():
        session = BotSession.query.filter_by(telegram_id=user.id).first()
        if not session or not session.is_authenticated:
            await update.message.reply_text(
                "🔒 يجب تسجيل الدخول أولاً!\n\nاستخدم /login"
            )
            update_statistics(increment_sent=True)
            return
        
        user_obj = User.query.get(session.user_id)
        
        if user_obj.role == 'student':
            student = Student.query.filter_by(user_id=user_obj.id).first()
            if student:
                my_courses = Enrollment.query.filter_by(student_id=student.id).count()
                total_grades = Grade.query.filter_by(student_id=student.id).count()
                
                dashboard_text = f"""
📊 *لوحة تحكم الطالب*

👤 الاسم: {student.full_name}
📱 الجوال: {student.phone_number}
📧 البريد: {student.email or 'غير محدد'}

📚 عدد الدورات: {my_courses}
📝 عدد الدرجات: {total_grades}

استخدم الأزرار أدناه للتصفح:
"""
                keyboard = [
                    [InlineKeyboardButton("📚 دوراتي", callback_data="my_courses")],
                    [InlineKeyboardButton("📖 دروسي", callback_data="my_lessons")],
                    [InlineKeyboardButton("📝 درجاتي", callback_data="my_grades")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    dashboard_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
                update_statistics(increment_sent=True)
        
        elif user_obj.role == 'teacher':
            teacher = Teacher.query.filter_by(user_id=user_obj.id).first()
            if teacher:
                my_enrollments = Enrollment.query.filter_by(teacher_id=teacher.id).count()
                my_students = Student.query.join(Enrollment).filter(
                    Enrollment.teacher_id == teacher.id
                ).distinct().count()
                my_lessons = Lesson.query.filter_by(teacher_id=teacher.id).count()
                
                dashboard_text = f"""
👨‍🏫 *لوحة تحكم المعلم*

👤 الاسم: {teacher.full_name}
📚 التخصص: {teacher.specialization or 'غير محدد'}
📖 عدد الدورات: {my_enrollments}
👥 عدد الطلاب: {my_students}
📝 عدد الدروس: {my_lessons}

استخدم الأزرار أدناه للتصفح:
"""
                keyboard = [
                    [InlineKeyboardButton("📚 دوراتي", callback_data="teacher_courses")],
                    [InlineKeyboardButton("📖 دروسي", callback_data="teacher_lessons")],
                    [InlineKeyboardButton("👥 طلابي", callback_data="teacher_students")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    dashboard_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
                update_statistics(increment_sent=True)
        
        elif user_obj.role in ['admin', 'assistant']:
            stats = {
                'students': Student.query.count(),
                'teachers': Teacher.query.count(),
                'courses': Course.query.count(),
                'enrollments': Enrollment.query.count()
            }
            
            dashboard_text = f"""
👑 *لوحة تحكم الإدارة*

👤 الاسم: {user_obj.name}
📋 الدور: {user_obj.role}

📊 *إحصائيات النظام:*
👨‍🎓 الطلاب: {stats['students']}
👨‍🏫 المعلمون: {stats['teachers']}
📚 الدورات: {stats['courses']}
📝 التسجيلات: {stats['enrollments']}
"""
            await update.message.reply_text(
                dashboard_text,
                parse_mode=ParseMode.MARKDOWN
            )
            update_statistics(increment_sent=True)

async def view_courses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    update_statistics()
    
    with flask_app.app_context():
        courses = Course.query.all()
        
        if not courses:
            await update.message.reply_text("لا توجد دورات متاحة حالياً")
            update_statistics(increment_sent=True)
            return
        
        await update.message.reply_text(
            f"📚 *الدورات المتاحة ({len(courses)})*\n\n"
            "اختر دورة لعرض التفاصيل:",
            parse_mode=ParseMode.MARKDOWN
        )
        update_statistics(increment_sent=True)
        
        for course in courses[:10]:
            enrolled_count = Enrollment.query.filter_by(course_id=course.id).count()
            available_seats = (course.max_students - enrolled_count) if course.max_students else "غير محدود"
            
            course_text = f"""
📖 *{course.name}*

📝 الوصف: {course.description[:100] if course.description else 'لا يوجد وصف'}...
⏱️ المدة: {course.duration}
💰 السعر: {course.price} ل.س
👥 المقاعد المتاحة: {available_seats}
"""
            
            keyboard = [[InlineKeyboardButton("عرض التفاصيل", callback_data=f"course_{course.id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                course_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            update_statistics(increment_sent=True)
            await asyncio.sleep(0.5)

async def view_news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    update_statistics()
    
    with flask_app.app_context():
        news_items = News.query.filter_by(is_published=True).order_by(
            News.created_at.desc()
        ).limit(5).all()
        
        if not news_items:
            await update.message.reply_text("لا توجد أخبار متاحة حالياً")
            update_statistics(increment_sent=True)
            return
        
        await update.message.reply_text(
            f"📰 *آخر الأخبار ({len(news_items)})*",
            parse_mode=ParseMode.MARKDOWN
        )
        update_statistics(increment_sent=True)
        
        for news in news_items:
            news_date = news.created_at.strftime('%Y-%m-%d')
            news_text = f"""
📰 *{news.title}*

📅 التاريخ: {news_date}

{news.content[:200]}...
"""
            
            keyboard = [[InlineKeyboardButton("قراءة المزيد", callback_data=f"news_{news.id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                news_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            update_statistics(increment_sent=True)
            await asyncio.sleep(0.5)

async def view_teachers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    update_statistics()
    
    with flask_app.app_context():
        teachers = Teacher.query.all()
        
        if not teachers:
            await update.message.reply_text("لا يوجد معلمون مسجلون حالياً")
            update_statistics(increment_sent=True)
            return
        
        await update.message.reply_text(
            f"👨‍🏫 *قائمة المعلمين ({len(teachers)})*",
            parse_mode=ParseMode.MARKDOWN
        )
        update_statistics(increment_sent=True)
        
        for teacher in teachers:
            teacher_text = f"""
👨‍🏫 *{teacher.full_name}*

📚 التخصص: {teacher.specialization or 'غير محدد'}
📜 المؤهلات: {teacher.qualifications or 'غير محدد'}
⏱️ الخبرة: {teacher.experience_years or 0} سنة
"""
            
            keyboard = [[InlineKeyboardButton("عرض التفاصيل", callback_data=f"teacher_{teacher.id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                teacher_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            update_statistics(increment_sent=True)
            await asyncio.sleep(0.5)

async def my_courses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    update_statistics()
    
    with flask_app.app_context():
        session = BotSession.query.filter_by(telegram_id=user.id).first()
        if not session or not session.is_authenticated:
            await update.message.reply_text(
                "🔒 يجب تسجيل الدخول أولاً!\n\nاستخدم /login"
            )
            update_statistics(increment_sent=True)
            return
        
        user_obj = User.query.get(session.user_id)
        
        if user_obj.role == 'student':
            student = Student.query.filter_by(user_id=user_obj.id).first()
            if student:
                enrollments = Enrollment.query.filter_by(student_id=student.id).all()
                
                if not enrollments:
                    await update.message.reply_text("أنت غير مسجل في أي دورة حالياً")
                    update_statistics(increment_sent=True)
                    return
                
                await update.message.reply_text(
                    f"📚 *دوراتي ({len(enrollments)})*",
                    parse_mode=ParseMode.MARKDOWN
                )
                update_statistics(increment_sent=True)
                
                for enrollment in enrollments:
                    course = enrollment.course
                    teacher = enrollment.teacher
                    lessons_count = Lesson.query.filter_by(
                        course_id=course.id,
                        is_published=True
                    ).count()
                    
                    course_text = f"""
📖 *{course.name}*

👨‍🏫 المعلم: {teacher.full_name if teacher else 'غير محدد'}
📝 عدد الدروس: {lessons_count}
⏱️ المدة: {course.duration}
"""
                    
                    keyboard = [[InlineKeyboardButton("عرض الدروس", callback_data=f"lessons_{course.id}")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        course_text,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=reply_markup
                    )
                    update_statistics(increment_sent=True)
                    await asyncio.sleep(0.5)

async def my_grades(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    update_statistics()
    
    with flask_app.app_context():
        session = BotSession.query.filter_by(telegram_id=user.id).first()
        if not session or not session.is_authenticated:
            await update.message.reply_text(
                "🔒 يجب تسجيل الدخول أولاً!\n\nاستخدم /login"
            )
            update_statistics(increment_sent=True)
            return
        
        user_obj = User.query.get(session.user_id)
        
        if user_obj.role == 'student':
            student = Student.query.filter_by(user_id=user_obj.id).first()
            if student:
                grades = Grade.query.filter_by(student_id=student.id).order_by(
                    Grade.created_at.desc()
                ).all()
                
                if not grades:
                    await update.message.reply_text("لا توجد درجات مسجلة لك حالياً")
                    update_statistics(increment_sent=True)
                    return
                
                grades_text = f"📝 *درجاتي ({len(grades)})*\n\n"
                
                for grade in grades[:20]:
                    course = grade.course
                    grade_date = grade.created_at.strftime('%Y-%m-%d')
                    grades_text += f"""
📚 {course.name}
📋 {grade.exam_name}
✅ الدرجة: {grade.score}/{grade.max_score}
📅 التاريخ: {grade_date}
━━━━━━━━━━━━━━━
"""
                
                await update.message.reply_text(
                    grades_text,
                    parse_mode=ParseMode.MARKDOWN
                )
                update_statistics(increment_sent=True)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    update_statistics()
    
    data = query.data
    
    if data.startswith('course_'):
        course_id = int(data.split('_')[1])
        with flask_app.app_context():
            course = Course.query.get(course_id)
            if course:
                enrolled_count = Enrollment.query.filter_by(course_id=course.id).count()
                available_seats = (course.max_students - enrolled_count) if course.max_students else "غير محدود"
                lessons_count = Lesson.query.filter_by(course_id=course.id, is_published=True).count()
                
                course_detail = f"""
📖 *{course.name}*

📝 *الوصف:*
{course.description or 'لا يوجد وصف'}

⏱️ المدة: {course.duration}
💰 السعر: {course.price} ل.س
📚 عدد الدروس: {lessons_count}
👥 المقاعد المتاحة: {available_seats}
{'⭐ دورة مميزة' if course.is_featured else ''}
"""
                await query.edit_message_text(
                    course_detail,
                    parse_mode=ParseMode.MARKDOWN
                )
                update_statistics(increment_sent=True)
    
    elif data.startswith('news_'):
        news_id = int(data.split('_')[1])
        with flask_app.app_context():
            news = News.query.get(news_id)
            if news:
                news_date = news.created_at.strftime('%Y-%m-%d %H:%M')
                news_detail = f"""
📰 *{news.title}*

📅 {news_date}

{news.content}
"""
                await query.edit_message_text(
                    news_detail,
                    parse_mode=ParseMode.MARKDOWN
                )
                update_statistics(increment_sent=True)
    
    elif data.startswith('teacher_'):
        teacher_id = int(data.split('_')[1])
        with flask_app.app_context():
            teacher = Teacher.query.get(teacher_id)
            if teacher:
                teacher_detail = f"""
👨‍🏫 *{teacher.full_name}*

📚 التخصص: {teacher.specialization or 'غير محدد'}
📜 المؤهلات: {teacher.qualifications or 'غير محدد'}
⏱️ الخبرة: {teacher.experience_years or 0} سنة
📧 البريد: {teacher.email or 'غير محدد'}
📱 الجوال: {teacher.phone_number or 'غير محدد'}

{teacher.bio or ''}
"""
                await query.edit_message_text(
                    teacher_detail,
                    parse_mode=ParseMode.MARKDOWN
                )
                update_statistics(increment_sent=True)
    
    elif data.startswith('lessons_'):
        course_id = int(data.split('_')[1])
        user = query.from_user
        
        with flask_app.app_context():
            session = BotSession.query.filter_by(telegram_id=user.id).first()
            if not session or not session.is_authenticated:
                await query.edit_message_text("🔒 يجب تسجيل الدخول أولاً!")
                update_statistics(increment_sent=True)
                return
            
            user_obj = User.query.get(session.user_id)
            student = Student.query.filter_by(user_id=user_obj.id).first()
            
            if not student:
                await query.edit_message_text("لم يتم العثور على ملف الطالب")
                update_statistics(increment_sent=True)
                return
            
            enrollment = Enrollment.query.filter_by(
                student_id=student.id,
                course_id=course_id
            ).first()
            
            if not enrollment:
                await query.edit_message_text("أنت غير مسجل في هذه الدورة")
                update_statistics(increment_sent=True)
                return
            
            course = Course.query.get(course_id)
            lessons = Lesson.query.filter_by(
                course_id=course_id,
                is_published=True
            ).all()
            
            if not lessons:
                await query.edit_message_text(f"لا توجد دروس متاحة في دورة {course.name}")
                update_statistics(increment_sent=True)
                return
            
            lessons_text = f"📖 *دروس دورة {course.name}*\n\n"
            
            for i, lesson in enumerate(lessons, 1):
                lesson_date = lesson.created_at.strftime('%Y-%m-%d')
                has_file = "📎" if lesson.file_path else ""
                lessons_text += f"{i}. {lesson.title} {has_file}\n"
                lessons_text += f"   📅 {lesson_date}\n\n"
            
            await query.edit_message_text(
                lessons_text,
                parse_mode=ParseMode.MARKDOWN
            )
            update_statistics(increment_sent=True)
    
    elif data == 'my_courses':
        await my_courses(query, context)
    
    elif data == 'my_grades':
        await my_grades(query, context)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    update_statistics()
    
    if text == "🔐 تسجيل الدخول":
        return await login_start(update, context)
    elif text == "📚 الدورات":
        return await view_courses(update, context)
    elif text == "📰 الأخبار":
        return await view_news(update, context)
    elif text == "👨‍🏫 المعلمون":
        return await view_teachers(update, context)
    elif text == "ℹ️ المساعدة":
        return await help_command(update, context)
    elif text == "📊 لوحة التحكم":
        return await dashboard(update, context)
    elif text == "📚 دوراتي":
        return await my_courses(update, context)
    elif text == "📝 درجاتي":
        return await my_grades(update, context)
    elif text == "🚪 تسجيل الخروج":
        return await logout(update, context)
    elif text == "📞 التواصل":
        with flask_app.app_context():
            settings = SiteSettings.query.first()
            contact_text = f"""
📞 *التواصل معنا*

{f'📱 الهاتف 1: {settings.phone1}' if settings and settings.phone1 else ''}
{f'📱 الهاتف 2: {settings.phone2}' if settings and settings.phone2 else ''}
{f'📧 البريد: {settings.email}' if settings and settings.email else ''}
{f'📍 العنوان: {settings.address}' if settings and settings.address else ''}
{f'📘 Facebook: {settings.facebook_url}' if settings and settings.facebook_url else ''}
"""
        await update.message.reply_text(contact_text, parse_mode=ParseMode.MARKDOWN)
        update_statistics(increment_sent=True)
    else:
        await update.message.reply_text(
            "عذراً، لم أفهم هذا الأمر.\n\n"
            "استخدم /help لعرض الأوامر المتاحة"
        )
        update_statistics(increment_sent=True)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Exception while handling an update: {context.error}")
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ عذراً، حدث خطأ غير متوقع.\n\n"
                "الرجاء المحاولة مرة أخرى أو استخدام /start"
            )
    except Exception as e:
        logger.error(f"Error in error handler: {e}")

async def send_notification_to_user(telegram_id: int, message: str):
    with flask_app.app_context():
        settings = SiteSettings.query.first()
        if not settings or not settings.telegram_bot_enabled:
            return False
        
        if not settings.telegram_bot_token:
            return False
        
        try:
            application = Application.builder().token(settings.telegram_bot_token).build()
            await application.bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            return True
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False

def main() -> None:
    with flask_app.app_context():
        settings = SiteSettings.query.first()
        if not settings or not settings.telegram_bot_token:
            logger.error("Telegram bot token not configured!")
            return
        
        if not settings.telegram_bot_enabled:
            logger.info("Telegram bot is disabled in settings")
            return
        
        token = settings.telegram_bot_token
    
    application = Application.builder().token(token).build()
    
    login_handler = ConversationHandler(
        entry_points=[CommandHandler('login', login_start)],
        states={
            LOGIN_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_phone)],
            LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(login_handler)
    application.add_handler(CommandHandler("logout", logout))
    application.add_handler(CommandHandler("dashboard", dashboard))
    application.add_handler(CommandHandler("courses", view_courses))
    application.add_handler(CommandHandler("news", view_news))
    application.add_handler(CommandHandler("teachers", view_teachers))
    application.add_handler(CommandHandler("mycourses", my_courses))
    application.add_handler(CommandHandler("mygrades", my_grades))
    
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    application.add_error_handler(error_handler)
    
    logger.info("Bot started successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
