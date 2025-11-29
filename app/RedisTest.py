import redis
r = redis.Redis(host="192.168.1.12", port=6379, db=0)
print(r.ping())