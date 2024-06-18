from django.contrib import admin

class MyAdminSite(admin.AdminSite):
    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        app_list += [
            {
                "name": "My Custom App",
                "app_label": "my_test_app",
                # "app_url": "/admin/test_view",
                "models": [
                    {
                        "name": "tcptraceroute",
                        "object_name": "tcptraceroute",
                        "admin_url": "/admin/test_view",
                        "view_only": True,
                    }
                ],
            }
        ]
        return app_list


mysite = MyAdminSite()
admin.site = mysite
