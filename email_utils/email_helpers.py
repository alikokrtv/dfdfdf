"""
E-posta içeriği oluşturma, gönderme ile ilgili yardımcı fonksiyonlar
"""
from flask import current_app, url_for

def get_app_url(endpoint, **kwargs):
    """
    E-postalar için doğru URL'yi oluşturan yardımcı fonksiyon.
    Config'deki BASE_URL değişkenini kullanarak doğru bağlantıları oluşturur.
    
    Parametreler:
        endpoint: Flask route endpoint adı (örn: 'dof.detail')
        **kwargs: URL parametreleri (örn: dof_id=5)
    
    Örnek kullanım:
    get_app_url('dof.detail', dof_id=5)
    """
    try:
        # Önce url_for ile path'i oluştur
        path = url_for(endpoint, **kwargs)
        
        # Sonra BASE_URL ile birleştir
        base_url = current_app.config.get('BASE_URL', 'http://localhost:5000/')
        
        # Base URL'in / ile bittiğinden emin ol
        if not base_url.endswith('/'):
            base_url += '/'
            
        # Path'in / ile başladığından emin ol, ancak çift / olmasın
        if path.startswith('/'):
            path = path[1:]
            
        # Tam URL'yi döndür
        return f"{base_url}{path}"
    except Exception as e:
        current_app.logger.error(f"URL oluşturma hatası: {str(e)}")
        # Hata durumunda en azından bir URL döndür
        fallback_url = current_app.config.get('BASE_URL', 'http://localhost:5000/')
        return fallback_url
