import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
backlog = 1024
timeout = 3000
keepalive = 360
graceful_timeout = 60
pidfile = "g.pid"
accesslog = "access.log"
errorlog = "error.log"
loglevel = "info"
daemon = True