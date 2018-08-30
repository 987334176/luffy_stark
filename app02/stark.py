# 这里的site,指的是实例化后的变量名
# StarkConfig表示类
from stark.server.stark import site,StarkConfig
from app02 import models
from django.conf.urls import url
from django.shortcuts import HttpResponse

class RoleConfig(StarkConfig):
    def sk2(self, request):
        return HttpResponse('sk2神仙水')

    def extra_url(self):
        data = [
            url(r'^sk2/$', self.sk2),
        ]
        return data

site.register(models.Role,RoleConfig)  # 注册表