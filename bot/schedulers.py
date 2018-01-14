
class Scheduler:

    def __init__(self,bot):
        self.bot=bot

    def ipos(self):
        print('ipos')
        self.bot.send_message('hi')