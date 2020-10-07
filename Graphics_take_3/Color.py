
from nmigen import Record

class Color(Record):
    def __init__(self, width=8):
        super().__init__([
            ("red", width),
            ("green", width),
            ("blue", width)])
    def as_concat(self):
        return Cat(self.red, self.green, self.blue)
    def as_list(self):
        return [self.red, self.green, self.blue]
    def eq(self, *color):
        if len(color)==1:
            return super().eq(color[0])
        elif len(color) == 3:
            r, g, b = color

        assert len(r)==len(g)==len(b)==len(self.red)
        return [
            self.red.eq(r),
            self.green.eq(g),
            self.blue.eq(b)]
