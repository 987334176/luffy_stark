import functools
from django.conf.urls import url
from django.shortcuts import HttpResponse,render,redirect
from types import FunctionType
from django.utils.safestring import mark_safe
from django.urls import reverse
from django import forms
from django.db.models import Q
from django.http import QueryDict

class ChangeList(object):
    """
    封装列表页面需要的所有功能
    """
    def __init__(self,config,queryset,q,search_list,page):
        ### 处理搜索 ###
        self.q = q  # 搜索条件
        self.search_list = search_list  # 搜索字段
        self.page = page  # 分页
        # 配置参数
        self.config = config
        # 批量操作
        self.action_list = [{'name': func.__name__, 'text': func.text} for func in config.get_action_list()]
        # 添加按钮
        self.add_btn = config.get_add_btn()
        # ORM执行结果
        self.queryset = queryset
        # 显示的列
        self.list_display = config.get_list_display()

class StarkConfig(object):
    def __init__(self,model_class,site):
        self.model_class = model_class
        self.site = site
        # 定义request变量,用于非视图函数使用。
        # 在wrapper装饰器中,对这个值重新赋值!
        self.request = None
        # url中的搜索条件,存在字典中。key为_filter
        self.back_condition_key = "_filter"

    def display_checkbox(self,row=None,header=False):  # 显示复选框
        if header:
            # 输出中文
            return "选择"
        # 注意：这里要写row.pk,不能写row.id。你不能保证每一个表的主键都是id
        return mark_safe("<input type='checkbox' name='pk' value='%s' />" % row.pk)

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

    def multi_delete(self, request):  # 批量删除
        """
        批量删除的action
        :param request:
        :return:
        """
        pk_list = request.POST.getlist('pk')
        self.model_class.objects.filter(pk__in=pk_list).delete()
        # return HttpResponse('删除成功')

    multi_delete.text = "批量删除"  # 添加自定义属性text

    def multi_init(self,request):  # 批量初始化
        print('批量初始化')

    multi_init.text = "批量初始化"  # 添加自定义属性text

    order_by = []  # 需要排序的字段,由用户自定义
    list_display = []  # 定义显示的列,由用户自定义
    model_form_class = None  # form组件需要的model_class
    action_list = []  # 批量操作方法
    # 搜索字段,如果是跨表字段,要按照ORM语法来
    search_list = []

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

    def get_action_list(self):  # 获取批量操作方法
        val = []  # 空列表
        # 扩展列表的元素
        val.extend(self.action_list)
        return val

    def get_action_dict(self):  # 获取匹配操作字典
        val = {}
        for item in self.action_list:
            # 以方法名为key
            val[item.__name__] = item
        return val

    def get_search_list(self):  # 获取搜索字段
        val = []
        val.extend(self.search_list)
        return val

    def get_search_condition(self, request):  # 根据关键字,组合ORM查询语句
        search_list = self.get_search_list()  # ['name','tel']
        q = request.GET.get('q', "")  # 搜索条件
        con = Q()
        con.connector = "OR"  # 以OR作为连接符
        if q:  # 判断条件不为空
            for field in search_list:
                # 合并条件进行查询, __contains表示使用like查询
                con.children.append(('%s__contains' % field, q))

        return search_list, q, con

    def changelist_view(self, request):
        """
        所有URL查看列表页面
        :param request:
        :return:
        """
        if request.method == 'POST':
            action_name = request.POST.get('action')
            action_dict = self.get_action_dict()
            if action_name not in action_dict:
                return HttpResponse('非法请求')

            response = getattr(self, action_name)(request)
            if response:
                return response

        ### 处理搜索 ###
        search_list, q, con = self.get_search_condition(request)
        # ##### 处理分页 #####
        from stark.utils.pagination import Pagination
        # 总条数
        total_count = self.model_class.objects.filter(con).count()
        # 复制GET参数
        query_params = request.GET.copy()
        # 允许编辑
        query_params._mutable = True
        # 使用分页类Pagination,传入参数。每页显示3条
        page = Pagination(request.GET.get('page'), total_count, request.path_info, query_params, per_page=3)

        # 根据排序列表进行排序,以及分页功能
        queryset = self.model_class.objects.filter(con).order_by(*self.get_order_by())[page.start:page.end]

        cl = ChangeList(self, queryset, q, search_list, page)
        context = {
            'cl': cl
        }

        # 注意:要传入参数
        return render(request,'stark/changelist.html',context)

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

    def wrapper(self, func):
        @functools.wraps(func)
        def inner(request, *args, **kwargs):
            self.request = request
            return func(request, *args, **kwargs)

        return inner

    def get_urls(self):
        info = self.model_class._meta.app_label, self.model_class._meta.model_name
        urlpatterns = [
            url(r'^list/$', self.wrapper(self.changelist_view), name='%s_%s_changelist' % info),
            url(r'^add/$', self.wrapper(self.add_view), name='%s_%s_add' % info),
            url(r'^(?P<pk>\d+)/change/', self.wrapper(self.change_view), name='%s_%s_change' % info),
            url(r'^(?P<pk>\d+)/del/', self.wrapper(self.delete_view), name='%s_%s_del' % info),
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

        # 获取当前请求的_filter参数,也就是跳转之前的搜索条件
        origin_condition = self.request.GET.get(self.back_condition_key)
        if not origin_condition:  # 如果没有获取到
            return list_url  # 返回列表页面

        # 列表地址和搜索条件拼接
        list_url = "%s?%s" % (list_url, origin_condition,)

        return list_url

    def reverse_add_url(self):  # 反向生成添加url
        app_label = self.model_class._meta.app_label
        model_name = self.model_class._meta.model_name
        namespace = self.site.namespace
        name = '%s:%s_%s_add' % (namespace, app_label, model_name)
        add_url = reverse(name)

        if not self.request.GET:  # 判断get参数为空
            return add_url  # 返回原url
        # request.GET的数据类型为QueryDict
        # 对QueryDict做urlencode编码
        param_str = self.request.GET.urlencode() # 比如q=xiao&age=20
        # 允许对QueryDict做修改
        new_query_dict = QueryDict(mutable=True)
        # 添加键值对. _filter = param_str
        new_query_dict[self.back_condition_key] = param_str
        # 添加url和搜索条件做拼接
        add_url = "%s?%s" % (add_url, new_query_dict.urlencode(),)
        # 返回最终url
        return add_url

    def reverse_edit_url(self, row):  # 反向生成编辑行内容的url
        app_label = self.model_class._meta.app_label  # app名
        model_name = self.model_class._meta.model_name  # 表名
        namespace = self.site.namespace  # 命名空间
        # 拼接字符串,这里为change
        name = '%s:%s_%s_change' % (namespace, app_label, model_name)
        # 反向生成url,传入参数pk=row.pk
        edit_url = reverse(name, kwargs={'pk': row.pk})

        if not self.request.GET:
            return edit_url
        param_str = self.request.GET.urlencode()
        new_query_dict = QueryDict(mutable=True)
        new_query_dict[self.back_condition_key] = param_str
        edit_url = "%s?%s" % (edit_url, new_query_dict.urlencode(),)

        return edit_url

    def reverse_del_url(self, row):  # 反向生成删除行内容的url
        app_label = self.model_class._meta.app_label
        model_name = self.model_class._meta.model_name
        namespace = self.site.namespace
        # 注意:这里为del
        name = '%s:%s_%s_del' % (namespace, app_label, model_name)
        del_url = reverse(name, kwargs={'pk': row.pk})

        if not self.request.GET:
            return del_url
        param_str = self.request.GET.urlencode()
        new_query_dict = QueryDict(mutable=True)
        new_query_dict[self.back_condition_key] = param_str
        del_url = "%s?%s" % (del_url, new_query_dict.urlencode(),)

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