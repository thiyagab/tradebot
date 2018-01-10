class Stock:
    def __init__(self,sym,ltp='',o='',h='',l='',c='',cp='',ltt=''):
        self.sym=sym
        self.ltp=ltp
        self.o = o
        self.h=h
        self.l=l
        self.c=c
        self.cp=cp
        self.ltt =ltt

    def __str__(self):
        try:
            str= self.html()
        except Exception as e:
            str=''
        return str;


    def html(self):
        return '<b>' + self.sym + ': ' + self.ltp + '</b> ( ' + self.cp + '% )\n' \
               + '<pre>' + self.ltt + '\n\n' \
               + 'o: ' + self.o + '\th: ' + self.h + '\n' \
                                          'l: ' + self.l+ \
               '\tc: ' +self.c + '</pre>\n\n' \

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
