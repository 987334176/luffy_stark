from django.conf.urls import url
from django.shortcuts import HttpResponse,render,redirect
from types import FunctionType
from django.utils.safestring import mark_safe
from django.urls import reverse
from django import forms

class StarkConfig(object):
    def __init__(self,model_class,site):
        self.model_class = model_class
        self.site = site

    def display_checkbox(self,row=None,header=False):  # 显示复选框
        if header:
            # 输出中文
            return "选择"
        # 注意：这里要写row.pk,不能写row.id。你不能保证每一个表的主键都是id
        return mark_safe('<input type="checkbox" name="pk" values="%s"/>' %row.pk)

    def display_edit(self, row=None, header=False):
        if header:
            return "编辑"

        return mark_safe(
            '<a href="%s"><i class="fa fa-edit" aria-hidden="true"></i></a></a>' % self.reverse_edit_url(row))

    def display_del(self, row=None, header=False):
        if header:
            return "删除"

        return mark_safe(
            '<a href="%s"><i class="fa fa-trash-o" aria-hidden="true"></i></a>' % self.reverse_del_url(row))

    def display_edit_del(self, row=None, header=False):
        if header:
            return "操作"
        tpl = """<a href="%s"><i class="fa fa-edit" aria-hidden="true"></i></a></a> |
        <a href="%s"><i class="fa fa-trash-o" aria-hidden="true"></i></a>
        """ % (self.reverse_edit_url(row), self.reverse_del_url(row),)
        return mark_safe(tpl)

    order_by = []  # 需要排序的字段,由用户自定义
    list_display = []  # 定义显示的列,由用户自定义
    model_form_class = None  # form组件需要的model_class

    def get_order_by(self):  # 获取排序列表
        return self.order_by

    def get_list_display(self):  # 获取显示的列
        return self.list_display

    def get_add_btn(self):  # 显示添加按钮
        return mark_safe('<a href="%s" class="btn btn-success">添加</a>' % self.reverse_add_url())

    def get_model_form_class(self):
        """
        获取ModelForm类
        :return:
        """
        if self.model_form_class:
            return self.model_form_class

        class AddModelForm(forms.ModelForm):
            class Meta:
                model = self.model_class
                fields = "__all__"

        return AddModelForm

    def changelist_view(self, request):
        """
        所有URL查看列表页面
        :param request:
        :return:
        """
        # 根据排序列表进行排序
        queryset = self.model_class.objects.all().order_by(*self.get_order_by())

        add_btn = self.get_add_btn()  # 添加按钮返回值,不为空展示,否则不展示

        list_display = self.list_display  # 定义显示的列
        header_list = []  # 定义头部,用来显示verbose_name
        if list_display:
            for name_or_func in list_display:
                if isinstance(name_or_func,FunctionType):
                    # 执行函数,默认显示中文
                    verbose_name = name_or_func(self,header=True)
                else:
                    # 获取指定字段的verbose_name
                    verbose_name = self.model_class._meta.get_field(name_or_func).verbose_name

                header_list.append(verbose_name)
        else:
            # 如果list_display为空,添加表名
            header_list.append(self.model_class._meta.model_name)

        body_list = []  # 显示内容

        for row in queryset:
            # 这里的row是对象，它表示表里面的一条数据
            row_list = []  # 展示每一行数据
            if not list_display:  # 如果不在list_display里面
                # 添加对象
                row_list.append(row)
                body_list.append(row_list)
                continue

            for name_or_func in list_display:
                if isinstance(name_or_func,FunctionType):
                    val = name_or_func(self,row=row)  # 执行函数获取,传递row对象
                else:
                    # 使用反射获取对象的值
                    val = getattr(row, name_or_func)

                row_list.append(val)

            body_list.append(row_list)

        # 注意:要传入add_btn
        return render(request,'stark/changelist.html',{'header_list':header_list,'body_list':body_list,'add_btn':add_btn})

    def add_view(self, request):
        """
        所有的添加页面,都在此方法处理
        使用ModelForm实现
        :param request:
        :return:
        """
        # 添加数据,使用ModelForm
        AddModelForm = self.get_model_form_class()

        if request.method == "GET":
            form = AddModelForm()
            return render(request,'stark/change.html',{'form':form})

        form = AddModelForm(request.POST)  # 接收POST数据
        if form.is_valid():  # 验证数据
            form.save()  # 自动保存数据
            # 反向生成url,跳转到列表页面
            return redirect(self.reverse_list_url())
        # 渲染页面,此时会保存表单数据
        return render(request, 'stark/change.html', {'form': form})

    def change_view(self, request, pk):
        """
        所有编辑页面
        :param request:
        :param pk:
        :return:
        """
        # 查看单条数据
        obj = self.model_class.objects.filter(pk=pk).first()
        if not obj:
            return HttpResponse('数据不存在')
        # 获取model_form类
        ModelFormClass = self.get_model_form_class()
        if request.method == 'GET':
            # instance表示生成默认值
            form = ModelFormClass(instance=obj)
            # 渲染页面,添加和修改可以共用一个一个模板文件
            return render(request, 'stark/change.html', {'form': form})
        # instance = obj 表示指定给谁做修改
        form = ModelFormClass(data=request.POST, instance=obj)
        if form.is_valid():
            form.save()  # 修改数据
            # 跳转到列表页面
            return redirect(self.reverse_list_url())
        return render(request, 'stark/change.html', {'form': form})

    def delete_view(self, request, pk):
        """
        所有删除页面
        :param request:
        :param pk:
        :return:
        """
        if request.method == "GET":
            # cancel_url表示用户点击取消时,跳转到列表页面
            return render(request, 'stark/delete.html', {'cancel_url': self.reverse_list_url()})
        # 定位单条数据,并删除!
        self.model_class.objects.filter(pk=pk).delete()
        return redirect(self.reverse_list_url())

    def wrapper(self,func):
        pass

    def get_urls(self):
        info = self.model_class._meta.app_label, self.model_class._meta.model_name
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

    def reverse_list_url(self):  # 反向生成访问列表的url
        app_label = self.model_class._meta.app_label
        model_name = self.model_class._meta.model_name
        namespace = self.site.namespace
        name = '%s:%s_%s_changelist' % (namespace, app_label, model_name)
        list_url = reverse(name)
        return list_url

    def reverse_add_url(self):  # 反向生成添加url
        app_label = self.model_class._meta.app_label
        model_name = self.model_class._meta.model_name
        namespace = self.site.namespace
        name = '%s:%s_%s_add' % (namespace, app_label, model_name)
        add_url = reverse(name)
        return add_url

    def reverse_edit_url(self, row):  # 反向生成编辑行内容的url
        app_label = self.model_class._meta.app_label  # app名
        model_name = self.model_class._meta.model_name  # 表名
        namespace = self.site.namespace  # 命名空间
        # 拼接字符串,这里为change
        name = '%s:%s_%s_change' % (namespace, app_label, model_name)
        # 反向生成url,传入参数pk=row.pk
        edit_url = reverse(name, kwargs={'pk': row.pk})
        return edit_url

    def reverse_del_url(self, row):  # 反向生成删除行内容的url
        app_label = self.model_class._meta.app_label
        model_name = self.model_class._meta.model_name
        namespace = self.site.namespace
        # 注意:这里为del
        name = '%s:%s_%s_del' % (namespace, app_label, model_name)
        del_url = reverse(name, kwargs={'pk': row.pk})
        return del_url

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