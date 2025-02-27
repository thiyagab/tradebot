from datetime import datetime


class Stock:
    def __init__(self, sym, ltp='', o='', h='', l='', c='', cp='', ltt='', name='', querysymbol=''):
        self.sym=sym
        self.ltp=ltp
        self.o = o
        self.h=h
        self.l=l
        self.c=c
        self.cp=cp
        self.ltt =ltt
        self.name=name
        self.querysymbol=querysymbol

    def __str__(self):
        try:
            str= self.html()
        except Exception as e:
            str=''
        return str;

    def shortview(self):
        return '<b>'+self.sym.upper()+' @ '+self.ltp+ '</b>\n'

    def formatltt(self):
        return datetime.strptime(self.ltt,'%d/%m/%Y  %H:%M:%S').strftime('%b %d, %H:%M')
    def html(self):
        return '<b>' + self.name.upper() + '</b>\n' \
               +'<pre>'+self.formatltt()+"</pre>\n\n"\
               +'<b>LTP    :   '+self.ltp+'  ( '+self.cp+'% )</b>\n\n' \
               +'<pre>' \
               +'o : '+self.o+'  h : '+self.h + '\n'\
               +'l : '+self.l+'  c : '+self.c + '</pre>\n\n' \

    def markup(self):
       return  """*{sym}: {ltp} ({cp}%)*
_{ltt}_

o: {o}   h: {h}
l: {l}   c: {c}

""".format(
            sym=self.sym,
            ltp=self.ltp,
            cp=self.cp,
            ltt=self.ltt,
            o=self.o,
            h=self.h,
            l=self.l,
            c=self.c
        )
