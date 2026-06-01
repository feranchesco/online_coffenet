from django.shortcuts import render

# Create your views here.
def admin_panel(request):
    return render(request, "admin_panel/management_panel.html",context={})