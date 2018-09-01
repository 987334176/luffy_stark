from stark.server.stark import site, StarkConfig
from app01 import models
from django import forms
from django.shortcuts import render
from django.conf.urls import url

class UserInfoConfig(StarkConfig):
    list_display = ['id', 'username']


class DepartModelForm(forms.ModelForm):
    class Meta:
        model = models.Depart
        fields = "__all__"

    def clean_name(self):  # 定义钩子
        # print(self.cleaned_data['name'])
        return self.cleaned_data['name']

class DepartConfig(StarkConfig):
    list_display = ['name', 'tel', 'user']
    # model_form_class = DepartModelForm
    def get_add_btn(self):  # 返回None,表示不显示添加按钮
        pass
    # def changelist_view(self, request):  # 重写changelist_view方法
    #     # 渲染自定义的列表页面
    #     return render(request,'stark/custom_list.html')
    def get_urls(self):
        info = self.model_class._meta.app_label, self.model_class._meta.model_name

        urlpatterns = [
            url(r'^list/$', self.changelist_view, name='%s_%s_changelist' % info),
        ]
        return urlpatterns

site.register(models.UserInfo, UserInfoConfig)
site.register(models.Depart, DepartConfig)
