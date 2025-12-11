import subprocess
import time
import sys, os
import datetime
from telegram import send_to_telegram
from dotenv import load_dotenv
from threading import Thread

load_dotenv()
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
def run_with_restart():
    restart_alarm = False
    while True:
        try:
            print(f"[{datetime.datetime.now()}] Запуск main.py...")

            process = subprocess.Popen(
                [sys.executable, "main.py"],
                stderr=subprocess.PIPE,
                text=True)
            process.wait()
            exit_code = process.returncode
            print(f"[{datetime.datetime.now()}] Скрипт упал (код: {exit_code}). Перезапуск через 3 секунды...")
            time.sleep(3)
                
        except KeyboardInterrupt:
            print(f"\n[{datetime.datetime.now()}] Остановлено пользователем")
            if process:
                process.terminate()
            break
        except Exception as e:
            print(f"[{datetime.datetime.now()}] Ошибка: {e}")
            time.sleep(3)

if __name__ == "__main__":
    run_with_restart()