import os
import shutil
import subprocess
from datetime import datetime
from flask import current_app
import asyncio
from telegram import Bot

class BackupManager:
    
    @staticmethod
    def create_full_backup():
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = f'backups/full_{timestamp}'
        os.makedirs(backup_dir, exist_ok=True)
        
        shutil.copy('alqasim_institute.db', f'{backup_dir}/database.db')
        
        if os.path.exists('app/static/uploads'):
            shutil.copytree('app/static/uploads', f'{backup_dir}/uploads')
        
        shutil.make_archive(f'backups/full_{timestamp}', 'zip', backup_dir)
        shutil.rmtree(backup_dir)
        
        return f'backups/full_{timestamp}.zip'
    
    @staticmethod
    def create_structure_backup():
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = f'backups/structure_{timestamp}'
        os.makedirs(backup_dir, exist_ok=True)
        
        subprocess.run([
            'sqlite3', 'alqasim_institute.db',
            '.schema > ' + f'{backup_dir}/schema.sql'
        ], shell=True)
        
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
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'backups/data_{timestamp}.db'
        os.makedirs('backups', exist_ok=True)
        
        shutil.copy('alqasim_institute.db', backup_file)
        
        return backup_file
    
    @staticmethod
    async def send_to_telegram(file_path):
        try:
            bot_token = current_app.config.get('TELEGRAM_BOT_TOKEN')
            chat_id = current_app.config.get('TELEGRAM_CHAT_ID')
            
            if not bot_token or not chat_id:
                return False
            
            bot = Bot(token=bot_token)
            
            with open(file_path, 'rb') as file:
                await bot.send_document(
                    chat_id=chat_id,
                    document=file,
                    caption=f'📦 نسخة احتياطية - {os.path.basename(file_path)}\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
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
        
        shutil.rmtree(temp_dir)
        return True
    
    @staticmethod
    def restore_data_backup(backup_file):
        shutil.copy(backup_file, 'alqasim_institute.db')
        return True
