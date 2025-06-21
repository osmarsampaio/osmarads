import os

# Nome do arquivo da aplicação
app = 'app:app'

# Número de workers (1 worker para evitar problemas com o SQLite)
workers = 1

# Usar o worker do eventlet para WebSockets
worker_class = 'eventlet'

# Número de threads por worker
threads = 4

# Endereço e porta (usar a porta da variável de ambiente PORT)
bind = '0.0.0.0:' + str(int(os.environ.get('PORT', '10000')))

# Timeout (aumentado para evitar timeouts em operações mais longas)
timeout = 120
keepalive = 5

# Nível de log
loglevel = 'info'

# Acesso ao log
accesslog = '-'

# Capturar erros
capture_output = True

# Habilitar o reload em desenvolvimento
reload = os.environ.get('FLASK_ENV') == 'development'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s'

# Log de erros
errorlog = '-'  # Saída para stderr

# Configurações de segurança
# Limita o tamanho do cabeçalho HTTP para prevenir ataques
limit_request_field_size = 4094
limit_request_fields = 100

# Configurações de desempenho
max_requests = 1000
max_requests_jitter = 50

# Habilita o modo de reinicialização do worker após um número de requisições
max_requests = 1000
max_requests_jitter = 50

# Configurações de socket
graceful_timeout = 30
