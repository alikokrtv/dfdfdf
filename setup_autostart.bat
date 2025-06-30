@echo off
echo DÖF Sistemi Otomatik Başlatma Kurulumu
echo =====================================

REM Başlangıç klasörünün yolunu al
set startup_folder=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

REM Mevcut dizini al
set current_dir=%~dp0

REM waitres.bat dosyasının tam yolunu oluştur
set waitres_path=%current_dir%waitres.bat

echo.
echo Başlangıç klasörü: %startup_folder%
echo DÖF Sistemi yolu: %waitres_path%

REM Başlangıç klasöründe kısayol oluştur
echo.
echo Kısayol oluşturuluyor...

REM PowerShell ile kısayol oluştur
powershell -Command "& {$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%startup_folder%\DÖF Sistemi.lnk'); $Shortcut.TargetPath = '%waitres_path%'; $Shortcut.WorkingDirectory = '%current_dir%'; $Shortcut.Description = 'DÖF Yönetim Sistemi Otomatik Başlatma'; $Shortcut.Save()}"

if %errorlevel% equ 0 (
    echo.
    echo ✅ BAŞARILI! DÖF Sistemi otomatik başlatma kuruldu.
    echo.
    echo 📋 Kontrol için:
    echo    - Windows + R → shell:startup → Enter
    echo    - "DÖF Sistemi.lnk" dosyasını göreceksiniz
    echo.
    echo 🚀 Bir sonraki PC yeniden başlatmada sistem otomatik açılacak!
    echo.
    echo 💡 Kaldırmak için: Başlangıç klasöründeki kısayolu silin
) else (
    echo.
    echo ❌ HATA! Kısayol oluşturulamadı.
    echo 💡 Bu dosyayı "Yönetici olarak çalıştır" ile deneyin.
)

echo.
pause 