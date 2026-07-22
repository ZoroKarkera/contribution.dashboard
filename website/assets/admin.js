const data = window.dashboardData;

function formatCurrency(amount) {
  return `${data.meta.currency_symbol}${Number(amount).toLocaleString("en-IN", {
    maximumFractionDigits: 0,
  })}`;
}

function renderPublicSummary() {
  const cards = [
    {
      label: "Target amount",
      value: data.public_summary.target_amount,
      meta: "Current fund goal",
      className: "summary-card--primary",
    },
    {
      label: "Already collected",
      value: data.public_summary.collected_amount,
      meta: `${data.summary.progress_percent}% of target reached`,
      className: "summary-card--primary",
    },
    ...data.public_summary.blocks.map((block) => ({
      label: `${block.wing} block amount`,
      value: block.formatted_amount,
      meta: `Collected from ${block.wing} block owners`,
      className: "summary-card--block",
    })),
    {
      label: "External sponsors amount",
      value: data.public_summary.external_sponsors_amount,
      meta: "Collected from sponsors",
      className: "summary-card--secondary",
    },
    {
      label: "Overall spent amount",
      value: data.public_summary.overall_spent_amount,
      meta: "Total deductions till now",
      className: "summary-card--expense",
    },
  ];

  document.getElementById("publicSummaryGrid").innerHTML = cards
    .map(
      (card) => `
        <article class="summary-card ${card.className}">
          <span class="summary-label">${card.label}</span>
          <strong class="summary-value">${card.value}</strong>
          <div class="summary-meta">${card.meta}</div>
        </article>
      `,
    )
    .join("");
}

function renderProgress() {
  document.getElementById("progressFill").style.width = `${Math.min(data.summary.progress_percent, 100)}%`;
  document.getElementById("progressPercent").textContent = `${data.summary.progress_percent}% complete`;
  document.getElementById("progressText").textContent = `${data.summary.formatted_total} raised of ${data.summary.formatted_goal}`;
}

function renderOwnerContributions() {
  const container = document.getElementById("ownerContributionsTable");
  container.innerHTML = `
    <table class="table">
      <thead>
        <tr>
          <th>Block</th>
          <th>Flat</th>
          <th>Owner</th>
          <th>Paid</th>
          <th>Payment Date</th>
          <th>Payment Mode</th>
          <th>Reference</th>
        </tr>
      </thead>
      <tbody>
        ${data.owners
          .map(
            (owner) => `
              <tr>
                <td>${owner.wing}</td>
                <td>${owner.flat}</td>
                <td>${owner.owner_name}</td>
                <td>${owner.formatted_paid_amount}</td>
                <td>${owner.last_payment_date || "-"}</td>
                <td>${owner.payment_mode || "-"}</td>
                <td>${owner.reference || "-"}</td>
              </tr>
            `,
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function renderSponsorContributions() {
  const container = document.getElementById("sponsorContributionsTable");
  container.innerHTML = `
    <table class="table">
      <thead>
        <tr>
          <th>Sponsor</th>
          <th>Received</th>
          <th>Payment Date</th>
          <th>Contact</th>
          <th>Reference</th>
        </tr>
      </thead>
      <tbody>
        ${data.sponsors
          .map(
            (sponsor) => `
              <tr>
                <td>${sponsor.sponsor_name}</td>
                <td>${sponsor.formatted_received_amount}</td>
                <td>${sponsor.received_date || "-"}</td>
                <td>${sponsor.phone || "-"}</td>
                <td>${sponsor.reference || "-"}</td>
              </tr>
            `,
          )
          .join("")}
      </tbody>
    </table>
  `;
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
                <td>${entry.formatted_amount}</td>
              </tr>
            `,
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function renderRecentContributions() {
  const container = document.getElementById("recentContributionsList");
  if (!data.recent_contributions.length) {
    container.innerHTML = '<p class="empty-state">No contribution records available yet.</p>';
    return;
  }

  container.innerHTML = `
    <div class="list">
      ${data.recent_contributions
        .map(
          (item) => `
            <div class="list-item">
              <div>
                <strong>${item.label}</strong>
                <span>${item.channel} · ${item.detail} · ${item.date}</span>
              </div>
              <div class="amount-pill">${formatCurrency(item.amount)}</div>
            </div>
          `,
        )
        .join("")}
    </div>
  `;
}

renderPublicSummary();
renderProgress();
renderOwnerContributions();
renderSponsorContributions();
renderDeductionsTable();
renderRecentContributions();
