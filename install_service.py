#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DÖF Sistemi Windows Service Kurulum Scripti
"""

import os
import sys
import subprocess

def create_service_script():
    """Windows Service için Python scripti oluşturur"""
    service_content = '''
import os
import sys
import time
import subprocess
import servicemanager
import win32serviceutil
import win32service
import win32event

class DOFSystemService(win32serviceutil.ServiceFramework):
    _svc_name_ = "DOFSystem"
    _svc_display_name_ = "DÖF Sistemi"
    _svc_description_ = "DÖF (Düzeltici/Önleyici Faaliyet) Yönetim Sistemi"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.process = None
        
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        if self.process:
            self.process.terminate()
            
    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        # DÖF sistemi çalıştır
        work_dir = r"C:\\Users\\aliko\\Desktop\\dfdfdf"
        os.chdir(work_dir)
        
        # Waitress ile sistemi başlat
        cmd = [sys.executable, "-m", "waitress", "--listen=*:5000", "wsgi:app"]
        
        try:
            self.process = subprocess.Popen(cmd, cwd=work_dir)
            
            # Servis durmasını bekle
            win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
            
        except Exception as e:
            servicemanager.LogErrorMsg(f"DÖF Sistemi başlatma hatası: {str(e)}")

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(DOFSystemService)
'''
    
    with open('dof_service.py', 'w', encoding='utf-8') as f:
        f.write(service_content)
    
    print("✅ dof_service.py oluşturuldu")

def install_service():
    """Windows Service'i kurar"""
    try:
        # Gerekli paketleri kur
        print("📦 Gerekli paketler kuruluyor...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pywin32"], check=True)
        
        # Service scripti oluştur
        create_service_script()
        
        # Service'i kur
        print("🔧 Windows Service kuruluyor...")
        subprocess.run([sys.executable, "dof_service.py", "install"], check=True)
        
        # Service'i başlat
        print("🚀 Service başlatılıyor...")
        subprocess.run([sys.executable, "dof_service.py", "start"], check=True)
        
        print("✅ DÖF Sistemi Windows Service olarak kuruldu!")
        print("📋 Kontrol için: services.msc açın ve 'DÖF Sistemi' servisini arayın")
        
    except Exception as e:
        print(f"❌ Hata: {str(e)}")
        print("💡 Scripti 'Yönetici olarak çalıştır' ile deneyin")

def uninstall_service():
    """Windows Service'i kaldırır"""
    try:
        subprocess.run([sys.executable, "dof_service.py", "remove"], check=True)
        print("✅ DÖF Sistemi Windows Service kaldırıldı!")
    except Exception as e:
        print(f"❌ Kaldırma hatası: {str(e)}")

if __name__ == "__main__":
    print("🏢 DÖF Sistemi Windows Service Kurulum")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        uninstall_service()
    else:
        install_service() 