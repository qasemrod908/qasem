import os
import shutil
import subprocess
from datetime import datetime
from flask import current_app
import asyncio
from telegram import Bot
from app.utils.helpers import damascus_now
import threading

class BackupManager:
    
    @staticmethod
    def create_auto_backup():
        try:
            BackupManager.create_full_backup()
            return True
        except Exception as e:
            print(f'خطأ في النسخ الاحتياطي التلقائي: {str(e)}')
            return False
    
    @staticmethod
    def create_full_backup():
        timestamp = damascus_now().strftime('%Y%m%d_%H%M%S')
        backup_dir = f'backups/full_{timestamp}'
        os.makedirs(backup_dir, exist_ok=True)
        
        shutil.copy('alqasim_institute.db', f'{backup_dir}/database.db')
        
        if os.path.exists('app/static/uploads'):
            shutil.copytree('app/static/uploads', f'{backup_dir}/uploads')
        
        if os.path.exists('app/templates'):
            shutil.copytree('app/templates', f'{backup_dir}/templates')
        
        if os.path.exists('app/static/css'):
            shutil.copytree('app/static/css', f'{backup_dir}/css')
        
        if os.path.exists('app/static/js'):
            shutil.copytree('app/static/js', f'{backup_dir}/js')
        
        if os.path.exists('app/static/images'):
            shutil.copytree('app/static/images', f'{backup_dir}/images')
        
        if os.path.exists('app/models'):
            shutil.copytree('app/models', f'{backup_dir}/models')
        
        if os.path.exists('app/routes'):
            shutil.copytree('app/routes', f'{backup_dir}/routes')
        
        if os.path.exists('app/utils'):
            shutil.copytree('app/utils', f'{backup_dir}/utils')
        
        important_files = ['run.py', 'requirements.txt', 'config.py', '.env']
        for file in important_files:
            if os.path.exists(file):
                shutil.copy(file, f'{backup_dir}/{file}')
        
        shutil.make_archive(f'backups/full_{timestamp}', 'zip', backup_dir)
        shutil.rmtree(backup_dir)
        
        return f'backups/full_{timestamp}.zip'
    
    @staticmethod
    def create_structure_backup():
        timestamp = damascus_now().strftime('%Y%m%d_%H%M%S')
        backup_dir = f'backups/structure_{timestamp}'
        os.makedirs(backup_dir, exist_ok=True)
        
        schema_file = f'{backup_dir}/schema.sql'
        with open(schema_file, 'w') as f:
            subprocess.run(
                ['sqlite3', 'alqasim_institute.db', '.schema'],
                stdout=f,
                stderr=subprocess.PIPE
            )
        
        if os.path.exists('app/templates'):
            shutil.copytree('app/templates', f'{backup_dir}/templates')
        if os.path.exists('app/static/css'):
            shutil.copytree('app/static/css', f'{backup_dir}/css')
        if os.path.exists('app/static/js'):
            shutil.copytree('app/static/js', f'{backup_dir}/js')
        
        shutil.make_archive(f'backups/structure_{timestamp}', 'zip', backup_dir)
        shutil.rmtree(backup_dir)
        
        return f'backups/structure_{timestamp}.zip'
    
    @staticmethod
    def create_data_backup():
        timestamp = damascus_now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'backups/data_{timestamp}.db'
        os.makedirs('backups', exist_ok=True)
        
        shutil.copy('alqasim_institute.db', backup_file)
        
        return backup_file
    
    @staticmethod
    async def send_to_telegram(file_path, bot_token, chat_id):
        try:
            if not bot_token or not chat_id:
                return False
            
            if not os.path.exists(file_path):
                print(f'الملف غير موجود: {file_path}')
                return False
            
            file_size = os.path.getsize(file_path)
            max_size = 50 * 1024 * 1024
            
            if file_size > max_size:
                print(f'حجم الملف ({file_size / 1024 / 1024:.2f} MB) أكبر من الحد المسموح (50 MB)')
                return False
            
            bot = Bot(token=bot_token)
            
            with open(file_path, 'rb') as file:
                await bot.send_document(
                    chat_id=chat_id,
                    document=file,
                    caption=f'📦 نسخة احتياطية - {os.path.basename(file_path)}\n📊 الحجم: {file_size / 1024 / 1024:.2f} MB\n⏰ التاريخ: {damascus_now().strftime("%Y-%m-%d %H:%M:%S")}',
                    read_timeout=120,
                    write_timeout=120,
                    connect_timeout=60
                )
            
            return True
        except Exception as e:
            print(f'خطأ في إرسال النسخة الاحتياطية إلى Telegram: {str(e)}')
            return False
    
    @staticmethod
    def restore_full_backup(backup_file):
        import zipfile
        temp_dir = 'temp_restore'
        
        with zipfile.ZipFile(backup_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        if os.path.exists(f'{temp_dir}/database.db'):
            shutil.copy(f'{temp_dir}/database.db', 'alqasim_institute.db')
        
        if os.path.exists(f'{temp_dir}/uploads'):
            if os.path.exists('app/static/uploads'):
                shutil.rmtree('app/static/uploads')
            shutil.copytree(f'{temp_dir}/uploads', 'app/static/uploads')
        
        if os.path.exists(f'{temp_dir}/templates'):
            if os.path.exists('app/templates'):
                shutil.rmtree('app/templates')
            shutil.copytree(f'{temp_dir}/templates', 'app/templates')
        
        if os.path.exists(f'{temp_dir}/css'):
            if os.path.exists('app/static/css'):
                shutil.rmtree('app/static/css')
            shutil.copytree(f'{temp_dir}/css', 'app/static/css')
        
        if os.path.exists(f'{temp_dir}/js'):
            if os.path.exists('app/static/js'):
                shutil.rmtree('app/static/js')
            shutil.copytree(f'{temp_dir}/js', 'app/static/js')
        
        if os.path.exists(f'{temp_dir}/images'):
            if os.path.exists('app/static/images'):
                shutil.rmtree('app/static/images')
            shutil.copytree(f'{temp_dir}/images', 'app/static/images')
        
        if os.path.exists(f'{temp_dir}/models'):
            if os.path.exists('app/models'):
                shutil.rmtree('app/models')
            shutil.copytree(f'{temp_dir}/models', 'app/models')
        
        if os.path.exists(f'{temp_dir}/routes'):
            if os.path.exists('app/routes'):
                shutil.rmtree('app/routes')
            shutil.copytree(f'{temp_dir}/routes', 'app/routes')
        
        if os.path.exists(f'{temp_dir}/utils'):
            if os.path.exists('app/utils'):
                shutil.rmtree('app/utils')
            shutil.copytree(f'{temp_dir}/utils', 'app/utils')
        
        important_files = ['run.py', 'requirements.txt', 'config.py']
        for file in important_files:
            if os.path.exists(f'{temp_dir}/{file}'):
                shutil.copy(f'{temp_dir}/{file}', file)
        
        shutil.rmtree(temp_dir)
        return True
    
    @staticmethod
    def restore_data_backup(backup_file):
        shutil.copy(backup_file, 'alqasim_institute.db')
        return True
    
    @staticmethod
    def restore_structure_backup(backup_file):
        import zipfile
        temp_dir = 'temp_restore'
        
        with zipfile.ZipFile(backup_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        if os.path.exists(f'{temp_dir}/templates'):
            if os.path.exists('app/templates'):
                shutil.rmtree('app/templates')
            shutil.copytree(f'{temp_dir}/templates', 'app/templates')
        
        if os.path.exists(f'{temp_dir}/css'):
            if os.path.exists('app/static/css'):
                shutil.rmtree('app/static/css')
            shutil.copytree(f'{temp_dir}/css', 'app/static/css')
        
        if os.path.exists(f'{temp_dir}/js'):
            if os.path.exists('app/static/js'):
                shutil.rmtree('app/static/js')
            shutil.copytree(f'{temp_dir}/js', 'app/static/js')
        
        shutil.rmtree(temp_dir)
        return True
    
    @staticmethod
    def list_backups():
        backups = []
        if os.path.exists('backups'):
            for filename in os.listdir('backups'):
                file_path = os.path.join('backups', filename)
                if os.path.isfile(file_path):
                    stat_info = os.stat(file_path)
                    backups.append({
                        'name': filename,
                        'path': file_path,
                        'size': stat_info.st_size,
                        'created': datetime.fromtimestamp(stat_info.st_ctime),
                        'type': BackupManager._get_backup_type(filename)
                    })
        backups.sort(key=lambda x: x['created'], reverse=True)
        return backups
    
    @staticmethod
    def _get_backup_type(filename):
        if filename.startswith('full_'):
            return 'شامل'
        elif filename.startswith('structure_'):
            return 'بنية'
        elif filename.startswith('data_'):
            return 'بيانات'
        else:
            return 'غير معروف'
    
    @staticmethod
    def delete_backup(filename):
        try:
            safe_filename = os.path.basename(filename)
            file_path = os.path.join('backups', safe_filename)
            abs_file_path = os.path.abspath(file_path)
            abs_backups_dir = os.path.abspath('backups')
            
            if not abs_file_path.startswith(abs_backups_dir + os.sep):
                raise ValueError('محاولة وصول غير مصرح بها')
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                os.remove(file_path)
                return True
            else:
                raise FileNotFoundError('الملف غير موجود')
        except Exception as e:
            raise Exception(f'خطأ في حذف النسخة الاحتياطية: {str(e)}')
