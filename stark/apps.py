from django.apps import AppConfig


class StarkConfig(AppConfig):
    name = 'stark'
    
    def ready(self):
        # 导入自动发现模块
        from django.utils.module_loading import autodiscover_modules
        # 查找每一个应用下的stark模块,也就是stark.py
        autodiscover_modules('stark')
