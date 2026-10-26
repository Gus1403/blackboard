// Checkpoint (s03)
(() => {
  scene('s03', (root, S) => {
    const h = S.header('Checkpoint', 'var(--blue)');
    const m = S.mcq({
      q: 'What is $\\langle 2,0\\rangle+\\langle 0,2\\rangle$?',
      opts: ['$\\langle 2,2\\rangle$', '$\\langle 4,0\\rangle$', '$\\langle 0,4\\rangle$', '$\\langle 2,0\\rangle$'],
      right: 'a',
      at: { show: S.at('q'), reveal: S.at('ans') },
    }, { marginTop: '40px' });
    const cd = S.countdown('think');
    return t => { S.show(h, t, 0.1); m.update(t); cd.update(t); };
  });
})();
