// Progressive enhancement: all records remain readable without JavaScript.
(() => {
  const nav = document.querySelector('.publication-tabs');
  if (!nav) return;
  const tabs = [...nav.querySelectorAll('a')];
  const panels = [...document.querySelectorAll('.publication-panel')];
  const patentIds = new Set(['patents', 'granted', 'applications', 'international']);
  nav.setAttribute('role', 'tablist');
  tabs.forEach((tab, i) => {
    tab.setAttribute('role', 'tab');
    tab.setAttribute('aria-controls', panels[i].id);
    panels[i].setAttribute('role', 'tabpanel');
    panels[i].setAttribute('aria-labelledby', tab.id);
    panels[i].tabIndex = 0;
    tab.addEventListener('click', event => {
      event.preventDefault();
      history.pushState(null, '', tab.hash);
      select(i);
    });
    tab.addEventListener('keydown', event => {
      if (event.ctrlKey || event.metaKey || event.altKey) return;
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (i + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
      tabs[next].focus();
      tabs[next].click();
    });
  });
  function select(index) {
    tabs.forEach((tab, i) => {
      tab.setAttribute('aria-selected', String(i === index));
      tab.tabIndex = i === index ? 0 : -1;
      panels[i].hidden = i !== index;
    });
  }
  function fromHash() {
    select(patentIds.has(location.hash.slice(1)) ? 1 : 0);
    const target = document.getElementById(location.hash.slice(1));
    if (target && !panels.includes(target)) target.scrollIntoView();
  }
  window.addEventListener('hashchange', fromHash);
  window.addEventListener('popstate', fromHash);
  fromHash();
})();
