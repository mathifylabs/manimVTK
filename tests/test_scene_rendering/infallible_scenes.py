from __future__ import annotations

from manimvtk import Scene, Square


class Wait1(Scene):
    def construct(self):
        self.wait()


class Wait2(Scene):
    def construct(self):
        self.add(Square())


class Wait3(Scene):
    def construct(self):
        self.wait(2)
