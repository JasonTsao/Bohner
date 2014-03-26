import redis
# import json
import os


class r:
    redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')  # this is for the heroku install!
    r = redis.from_url(redis_url)

    def expire_old_in_range(self, min_r, max_r):
        max_r = max_r + 1
        for x in range(min_r, max_r):
            y = self.r.get(x)
            z = self.r.hgetall(str(x) + ".view.hash")
            if y:
                if z:
                    # add to the list to be evaluated again
                    print "Should add " + str(x) + " back to the queue"
                    self.r.rpush("views", x)
                else:
                    print "Yes on y no on z. Should expire " + str(x)
                    self.r.expire(x, 10)
                    self.r.expire(str(x) + ".view.hash", 10)
            else:
                print "Not even a y. Should expire " + str(x)
                self.r.expire(x, 10)
                self.r.expire(str(x) + ".view.hash", 10)