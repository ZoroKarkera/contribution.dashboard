const data = window.dashboardData;

function renderPublicSummary() {
  const cards = [
    {
      label: "Target amount",
      value: data.public_summary.target_amount,
      meta: "Current fund goal",
    },
    {
      label: "Already collected",
      value: data.public_summary.collected_amount,
      meta: `${data.summary.progress_percent}% of target reached`,
    },
    ...data.public_summary.blocks.map((block) => ({
      label: `${block.wing} block amount`,
      value: block.formatted_amount,
      meta: `Collected from ${block.wing} block owners`,
    })),
    {
      label: "External sponsors amount",
      value: data.public_summary.external_sponsors_amount,
      meta: "Collected from sponsors",
    },
    {
      label: "Overall spent amount",
      value: data.public_summary.overall_spent_amount,
      meta: "Total deductions till now",
    },
  ];

  document.getElementById("publicSummaryGrid").innerHTML = cards
    .map(
      (card) => `
        <article class="summary-card">
          <span class="summary-label">${card.label}</span>
          <strong class="summary-value">${card.value}</strong>
          <div class="summary-meta">${card.meta}</div>
        </article>
      `,
    )
    .join("");
}

function renderDeductionsTable() {
  const container = document.getElementById("deductionsTable");
  if (!data.deductions_recent.length) {
    container.innerHTML = '<p class="empty-state">No deductions recorded yet.</p>';
    return;
  }

  container.innerHTML = `
    <table class="table">
      <thead>
        <tr>
          <th>Date</th>
          <th>Category</th>
          <th>Description</th>
          <th>Amount</th>
        </tr>
      </thead>
      <tbody>
        ${data.deductions_recent
          .map(
            (entry) => `
              <tr>
                <td>${entry.entry_date}</td>
                <td>${entry.category}</td>
                <td>${entry.description}</td>
                <td>${entry.formatted_amount}</td>
              </tr>
            `,
          )
          .join("")}
      </tbody>
    </table>
  `;
}

renderPublicSummary();
renderDeductionsTable();
