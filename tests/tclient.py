import pyjulius3
import queue

class Clinet(object):
    def __init__(self):
        self.client = pyjulius3.Client('localhost', 10500)

    def start(self):
        self.client.connect()
        self.client.start()

    def stop(self):
        self.client.stop()
        self.client.join()
        self.client.disconnect()


c = Clinet()
c.client.send('なに も 変化 が あり ませ ん 。')
try:
    while 1:
        try:
            result = c.client.results.get(False)
        except queue.Empty:
            continue
        print(repr(result))
except KeyboardInterrupt:
    print('Exiting...')
    c.stop()
else:
    c.stop()
