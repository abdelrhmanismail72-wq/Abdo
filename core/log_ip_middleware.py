class LogIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get('REMOTE_ADDR')
        path = request.path
        print(f"📡 New Request From IP: {ip} | المسار: {path}")
        return self.get_response(request)