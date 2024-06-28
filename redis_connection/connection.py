import redis
import os
import traceback
from redis.exceptions import RedisError


class RedisConnection:
    def __init__(self):
        try:
            password = 'admin'  # os.getenv('PASSWORD')
            if not (password and password.strip()):
                self.client = redis.Redis(
                    host=os.getenv('HOST', "localhost"),
                    port=os.getenv('PORT', 6379),
                    decode_responses=True)
            else:
                self.client = redis.Redis(
                    host=os.getenv('HOST', "localhost"),
                    port=os.getenv('PORT', 6379),
                    password=password,
                    decode_responses=True)
            self.client.ping()
        except RedisError as e:
            traceback.print_exc()
            raise Exception('Redis unavailable')

    def get_connection(self):
        return self.client


if __name__ == "__main__":
    redis_conn = RedisConnection()
    conn = redis_conn.get_connection()
    if conn:
        conn.set('key', 'value')
        print(conn.get('key'))
