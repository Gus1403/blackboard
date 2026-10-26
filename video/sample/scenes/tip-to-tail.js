// Chapter 1 (s01 card, s02 tip-to-tail sum)
(() => {
  scene('s01', (root, S) => S.chapterCard(1, 'Tip to tail', 'components add separately'));

  scene('s02', (root, S) => {
    const f = S.fig({ x: 100, y: 120, w: 820, h: 800, xr: [-0.5, 5], yr: [-0.5, 4] });
    const d = S.deriv([
      { l: '\\vec A+\\vec B', r: '=\\langle 3+1,\\;1+2\\rangle', why: 'add components', at: S.at('c') },
      { l: '', r: '=\\langle 4,3\\rangle', at: S.at('c') + 1, box: true },
    ], { position: 'absolute', left: '1000px', top: '420px' });
    return t => {
      f.clear(); f.grid(0.6); f.axes({ xl: 'x', yl: 'y', ticks: true });
      f.arrow(0, 0, 3, 1, '#6fa8dc', 6, S.p(t, S.at('a'), 0.8));
      f.arrow(3, 1, 4, 3, '#e3b35a', 6, S.p(t, S.at('b'), 0.8));
      f.arrow(0, 0, 4, 3, '#5fbf86', 6, S.p(t, S.at('c'), 0.8));
      if (t > S.at('a') + 0.8) f.text('A', 1.6, 0.45, { col: '#6fa8dc', size: 40, dy: 18 });
      if (t > S.at('b') + 0.8) f.text('B', 3.6, 1.9, { col: '#e3b35a', size: 40, dx: 28 });
      d.update(t);
    };
  });
})();
