import redis

ssl_ca_certs = 'config/redis_ca.pem'

if __name__ == '__main__':
    # r = redis.Redis(
    #     host='redis-14037.c301.ap-south-1-1.ec2.redns.redis-cloud.com',
    #     port=14037,
    #     ssl=True,
    #     password='admin',
    #     ssl_ca_certs=ssl_ca_certs
    # )
    # print(r.ping())
    #if(not (test_str1 and test_str1.strip())):
    # with open('/Users/abhishek/apps/Work/test/Big_file/random_text_1_1MB.txt', 'r') as file:
    #     data = file.read().rstrip()
    #
    # r.set(data, "World!!!")
    # print(r.get(data))

    s = 'NULL'
    if (not (s and s.strip())):
        print('true')