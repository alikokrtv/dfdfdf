import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
max_requests = 1000
timeout = 120
worker_class = "gevent"
keep_alive = 5
accesslog = "-"
errorlog = "-"
loglevel = "info"
reload = True
