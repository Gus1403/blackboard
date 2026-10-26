// Title card (s00)
(() => {
  scene('s00', (root, S) => {
    const wrap = S.el('div', 'abs', null, root, { left: '0', right: '0', top: '300px', textAlign: 'center' });
    const kick = S.el('div', 'tag', 'Sample lesson', wrap, { color: 'var(--acc)' });
    const title = S.el('div', 'h-display', window.TIMELINE.title, wrap, { fontSize: '120px', marginTop: '34px' });
    const hook = S.el('div', 'dim', 'tip to tail', wrap, { fontSize: '48px', marginTop: '28px', fontStyle: 'italic' });
    return t => { S.show(kick, t, 0.1); S.show(title, t, 0.35, { dy: 30 }); S.show(hook, t, S.at('a') + 1); };
  });
})();
