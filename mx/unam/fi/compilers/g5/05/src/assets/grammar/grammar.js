const search = document.querySelector('#search');
const cards = [...document.querySelectorAll('.grammar-card')];
const rows = [...document.querySelectorAll('tbody tr')];
const count = document.querySelector('#visible-count');

function applyFilter() {
  const q = search.value.trim().toLowerCase();
  let visible = 0;

  cards.forEach(card => {
    const cardMatch = card.dataset.search.includes(q);
    const alts = [...card.querySelectorAll('.alt')];
    let visibleAlts = 0;

    alts.forEach(alt => {
      const ok = !q || cardMatch || alt.dataset.search.includes(q);
      alt.classList.toggle('hidden', !ok);
      if (ok) visibleAlts++;
    });

    const show = visibleAlts > 0;
    card.classList.toggle('hidden', !show);
    if (show) visible++;
  });

  rows.forEach(row => row.classList.toggle('hidden', q && !row.dataset.search.includes(q)));
  count.textContent = visible;
}

search.addEventListener('input', applyFilter);
applyFilter();
