"""Single model owner; threaded requests preserve cancellation and batch APIs."""
import os
bind = os.environ.get('TEMPO_BIND', '0.0.0.0:7860')
workers = 1
threads = 4
timeout = 600
graceful_timeout = 30
accesslog = '-'
errorlog = '-'
capture_output = True
