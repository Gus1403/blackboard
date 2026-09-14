"""Math Board manim scenes. Render:
  manim -qm -o riemann.mp4 scenes.py RiemannRight      (animation)
  manim -s -qh -o riemann_frame.png scenes.py RiemannRight   (last frame PNG)
"""
from manim import *

config.background_color = "#141414"

ACCENT = "#7cc06c"
BLUE_ = "#6c9ccf"
RED_ = "#e06666"


def f(x):
    return x ** 2 - 2


class RiemannRight(Scene):
    """f(x)=x^2-2 on [3,6], right-endpoint rectangles refining n=4 -> 8 -> 16 -> 32."""

    def construct(self):
        ax = Axes(
            x_range=[0, 6.8, 1],
            y_range=[0, 36, 8],
            x_length=10,
            y_length=5.6,
            axis_config={"color": GREY_B, "include_tip": False},
        ).to_edge(DOWN)
        labels = VGroup(Text("x", font_size=26, color=GREY_A).next_to(ax.x_axis.get_end(), RIGHT),
                        Text("f(x)", font_size=26, color=GREY_A).next_to(ax.y_axis.get_end(), UP))
        graph = ax.plot(f, x_range=[0, 6.1], color=BLUE_)
        title = Text("f(x) = x² − 2 on [3,6], right endpoints", font_size=30).to_edge(UP)

        # mark [3,6]
        marks = VGroup(*[
            VGroup(DashedLine(ax.c2p(x, 0), ax.c2p(x, f(x)), color=GREY_C),
                   Text(str(x), font_size=26, color=GREY_A).next_to(ax.c2p(x, 0), DOWN))
            for x in (3, 6)
        ])

        self.add(ax, labels, graph, title, marks)

        n_label = Text("n = 4", font_size=34, color=ACCENT).to_corner(UR).shift(DOWN * 0.6)
        rects = ax.get_riemann_rectangles(
            graph, x_range=[3, 6], dx=3 / 4, input_sample_type="right",
            color=[ACCENT, BLUE_], fill_opacity=0.55, stroke_width=1,
        )
        self.play(Create(rects), FadeIn(n_label))
        self.wait(0.8)

        for n in (8, 16, 32):
            new_rects = ax.get_riemann_rectangles(
                graph, x_range=[3, 6], dx=3 / n, input_sample_type="right",
                color=[ACCENT, BLUE_], fill_opacity=0.55, stroke_width=1,
            )
            new_label = Text(f"n = {n}", font_size=34, color=ACCENT).move_to(n_label)
            self.play(Transform(rects, new_rects), Transform(n_label, new_label), run_time=1.2)
            self.wait(0.6)

        area = Text("→ ∫₃⁶ (x² − 2) dx", font_size=30, color=ACCENT)
        area.next_to(n_label, DOWN, aligned_edge=RIGHT)
        self.play(Write(area))
        self.wait(1.5)


class RightEndpointCheck(Scene):
    """Static: one subinterval strip showing x_i* = 3 + 3i/n, and i=n landing on 6."""

    def construct(self):
        ax = Axes(
            x_range=[2.5, 6.5, 1],
            y_range=[0, 36, 8],
            x_length=10,
            y_length=5.2,
            axis_config={"color": GREY_B, "include_tip": False},
        ).to_edge(DOWN)
        graph = ax.plot(f, x_range=[2.5, 6.2], color=BLUE_)
        n = 6
        rects = ax.get_riemann_rectangles(
            graph, x_range=[3, 6], dx=3 / n, input_sample_type="right",
            color=[GREY_D], fill_opacity=0.25, stroke_width=1,
        )
        # highlight the i-th rectangle (i=3)
        i = 3
        hi = ax.get_riemann_rectangles(
            graph, x_range=[3 + (i - 1) * 3 / n, 3 + i * 3 / n], dx=3 / n,
            input_sample_type="right", color=[ACCENT], fill_opacity=0.7, stroke_width=1,
        )
        xi = 3 + i * 3 / n
        dot = Dot(ax.c2p(xi, f(xi)), color=RED_)
        lab = Text("xᵢ* = 3 + 3i/n", font_size=30, color=RED_)
        lab.next_to(dot, UR, buff=0.3)
        check = Text("i = n:  xₙ* = 3 + 3n/n = 6  ✓", font_size=28, color=GREY_A).to_edge(UP)
        for x, t in ((3, "3"), (6, "6")):
            self.add(Text(t, font_size=26, color=GREY_A).next_to(ax.c2p(x, 0), DOWN))
        self.add(ax, graph, rects, hi, dot, lab, check)


class BankTAccounts(Scene):
    """Lesson 0001 (how a bank works): the bank's books before and after an $80 loan."""

    def construct(self):
        self.camera.background_color = "#0c0c0c"
        CH, HI, DIM = "#e9e6df", "#9b3a4a", "#8a8a84"

        def taccount(title, left, right, hi=()):
            w, h = 6.2, 2.6
            top = Line(LEFT * w / 2, RIGHT * w / 2, color=CH, stroke_width=3)
            mid = Line(ORIGIN, DOWN * h, color=CH, stroke_width=3)
            t = Text(title, font_size=34, color=CH).next_to(top, UP, buff=0.3)
            la = Text("owns / is owed", font_size=22, color=DIM).next_to(top, DOWN, buff=0.15).shift(LEFT * w / 4)
            lb = Text("owes", font_size=22, color=DIM).next_to(top, DOWN, buff=0.15).shift(RIGHT * w / 4)
            g = VGroup(top, mid, t, la, lb)

            def col(items, x0, x1):
                for i, (name, amt) in enumerate(items):
                    c = HI if name in hi else CH
                    y = DOWN * (1.0 + 0.65 * i)
                    n = Text(name, font_size=30, color=c)
                    a = Text(amt, font_size=30, color=c)
                    n.move_to(RIGHT * x0 + y, aligned_edge=LEFT)
                    a.move_to(RIGHT * x1 + y, aligned_edge=RIGHT)
                    g.add(n, a)

            col(left, -w / 2 + 0.15, -0.3)
            col(right, 0.3, w / 2 - 0.15)
            lt = sum(int(a.strip("$")) for _, a in left)
            rt = sum(int(a.strip("$")) for _, a in right)
            tl = Text(f"${lt}", font_size=26, color=DIM).move_to(mid.get_end() + LEFT * 0.3 + DOWN * 0.3, aligned_edge=RIGHT)
            tr = Text(f"${rt}", font_size=26, color=DIM).move_to(mid.get_end() + RIGHT * 0.3 + DOWN * 0.3, aligned_edge=LEFT)
            g.add(tl, tr)
            return g

        before = taccount("Before the loan",
                          [("Cash", "$110")],
                          [("Deposits", "$100"), ("Owners", "$10")])
        after = taccount("After the loan",
                         [("Cash", "$110"), ("Loan", "$80")],
                         [("Deposits", "$180"), ("Owners", "$10")],
                         hi=("Loan", "Deposits"))
        before.move_to(LEFT * 3.5 + UP * 0.4)
        after.move_to(RIGHT * 3.5 + UP * 0.4)
        arrow = Arrow(LEFT * 0.35, RIGHT * 0.35, color=DIM, buff=0, max_tip_length_to_length_ratio=0.35).move_to(UP * 0.1)
        note = Text("the bank writes +$80 on both sides", font_size=26, color=HI).next_to(VGroup(before, after), DOWN, buff=0.6)
        self.add(before, after, arrow, note)
