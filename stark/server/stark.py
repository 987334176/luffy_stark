from django.conf.urls import url
from django.shortcuts import HttpResponse

class StarkConfig(object):
    def __init__(self,model_class,site):
        self.model_class = model_class
        self.site = site

    def changelist_view(self, request):
        """
        所有URL查看列表页面
        :param request:
        :return:
        """
        return HttpResponse('stark list')

    def add_view(self, request):
        return HttpResponse('stark add')

    def change_view(self, request, pk):
        return HttpResponse('stark change')

    def delete_view(self, request, pk):
        return HttpResponse('stark delete')

    def wrapper(self,func):
        pass

    def get_urls(self):
        info = self.model_class._meta.app_label, self.model_class._meta.model_name
        # print(info)
        urlpatterns = [
            url(r'^list/$', self.changelist_view, name='%s_%s_changelist' % info),
            url(r'^add/$', self.add_view, name='%s_%s_add' % info),
            url(r'^(?P<pk>\d+)/change/', self.change_view, name='%s_%s_change' % info),
            url(r'^(?P<pk>\d+)/del/', self.delete_view, name='%s_%s_del' % info),
        ]

        extra = self.extra_url()
        if extra:  # 判断变量不为空
            # 扩展路由
            urlpatterns.extend(extra)

        # print(urlpatterns)
        return urlpatterns

    def extra_url(self):  # 额外的路由,由调用者重构
        pass

    @property
    def urls(self):
        return self.get_urls()

class AdminSite(object):
    def __init__(self):
        self._registry = {}
        self.app_name = 'stark'
        self.namespace = 'stark'

    def register(self,model_class,stark_config=None):
        # not None的结果为Ture
        if not stark_config:
            # 也就是说,当其他应用调用register时,如果不指定stark_config参数
            # 那么必然执行下面这段代码！
            # stark_config和StarkConfig是等值的！都能实例化
            stark_config = StarkConfig

        # 添加键值对,实例化类StarkConfig,传入参数model_class
        # self指的是AdminSite类
        self._registry[model_class] = stark_config(model_class,self)

        # print(self._registry)  # 打印字典
        """
        {
            app01.models.UserInfo:StarkConfig(app01.models.UserInfo)
            app02.models.Role:RoleConfig(app02.models.Role)
        }
        """

        # for k, v in self._registry.items():
        #     print(k,v)

    def get_urls(self):
        urlpatterns = []

        for k, v in self._registry.items():
            # k=modes.UserInfo,v=StarkConfig(models.UserInfo), # 封装：model_class=UserInfo，site=site对象
            # k=modes.Role,v=RoleConfig(models.Role)           # 封装：model_class=Role，site=site对象
            app_label = k._meta.app_label
            model_name = k._meta.model_name
            urlpatterns.append(url(r'^%s/%s/' % (app_label, model_name,), (v.urls, None, None)))

        return urlpatterns

    @property
    def urls(self):
        # 调用get_urls方法
        # self.app_name和self.namespace值是一样的,都是stark
        return self.get_urls(), self.app_name, self.namespace

site = AdminSite()  # 实例化类