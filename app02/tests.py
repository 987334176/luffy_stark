from django.test import TestCase

# Create your tests here.
'''

info = self.model_class._meta.app_label, self.model_class._meta.model_name
urlpatterns = [
    url(r'^list/$', self.changelist_view, name='%s_%s_changelist' % info),
    ...
]
class xxxModelForm(ModelForm):
    class Meta:
        model = xxx
        field = ['id','xx']
'''