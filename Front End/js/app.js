// frontend/js/app.js
const API_BASE = ""; // same origin (served by your backend) or set full URL if different
let contractInfo = null;
let userAccount = null;
let provider, signer, contract;

const socket = io(); // connect to same host

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("connectWalletBtn").addEventListener("click", connectWallet);
  document.getElementById("submitReportBtn").addEventListener("click", submitReport);
  document.getElementById("viewAllBtn").addEventListener("click", openAllReports);
  document.getElementById("closeAll").addEventListener("click", () => document.getElementById("allModal").classList.remove("open"));

  init();
});

async function init() {
  await loadContractInfo();
  await loadStats();
  setupSocket();
}

async function loadContractInfo() {
  try {
    const r = await fetch("/api/contract-info");
    contractInfo = await r.json();
    // If you want frontend to call contract directly:
    provider = (window.ethereum) ? new ethers.providers.Web3Provider(window.ethereum) : new ethers.providers.InfuraProvider("sepolia");
    contract = new ethers.Contract(contractInfo.address, contractInfo.abi, provider);
  } catch (e) {
    console.error("Could not load contract info", e);
  }
}

async function connectWallet() {
  if (!window.ethereum) return alert("Please install MetaMask (or compatible wallet)");
  try {
    await window.ethereum.request({ method: "eth_requestAccounts" });
    const accounts = await window.ethereum.request({ method: "eth_accounts" });
    userAccount = accounts[0];
    document.getElementById("walletAddress").innerText = `Connected: ${userAccount.substring(0,6)}...${userAccount.slice(-4)}`;
    loadUserReports();
  } catch (e) {
    console.error("Wallet error", e);
    alert("Wallet connection failed");
  }
}

async function submitReport() {
  if (!userAccount) {
    return alert("Please connect your wallet first.");
  }
  const description = document.getElementById("description").value.trim();
  const category = document.getElementById("category").value;
  const location = document.getElementById("location").value.trim();

  if (!description || !location) return alert("Please provide description and location");

  const statusEl = document.getElementById("submitStatus");
  statusEl.innerText = "Submitting...";

  try {
    const body = { description, category, location, user: userAccount };
    const res = await fetch("/api/report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (data.success) {
      Toastify({ text: "Report submitted! AI response received.", duration: 5000 }).showToast();
      statusEl.innerText = data.ai_response;
      // clear form
      document.getElementById("description").value = "";
      // refresh stats & lists
      await loadStats();
      await loadUserReports();
    } else {
      statusEl.innerText = "Submission failed";
    }
  } catch (e) {
    console.error("Submit failed", e);
    statusEl.innerText = "Error submitting";
  } finally {
    setTimeout(()=> statusEl.innerText = "", 6000);
  }
}

async function loadStats() {
  try {
    const r = await fetch("/api/reports/stats");
    const j = await r.json();
    document.getElementById("totalReports").innerText = j.totalReports ?? 0;
    document.getElementById("uniqueReporters").innerText = j.uniqueReporters ?? 0;
  } catch (e) {
    console.warn("Could not load stats", e);
  }
}

async function loadUserReports() {
  if (!userAccount) return;
  try {
    const r = await fetch(`/api/reports/user/${userAccount}`);
    const arr = await r.json();
    const container = document.getElementById("myReports");
    container.innerHTML = "";
    if (arr.length === 0) container.innerHTML = "<div class='muted'>You have not submitted any reports yet.</div>";
    arr.forEach(item => {
      const d = document.createElement("div");
      d.className = "report-card";
      d.innerHTML = `<strong>${item.category}</strong> — ${item.location}<div style="margin-top:6px">${item.description}</div>
        <div style="margin-top:6px"><small>AI: ${item.ai_response ?? "—"}</small></div>
        <div style="margin-top:6px"><small>Tx: ${item.tx_hash ? item.tx_hash.substring(0,12) + "..." : "pending"}</small></div>`;
      container.appendChild(d);
    });
  } catch(e) { console.error("Load user reports error", e); }
}

async function openAllReports() {
  try {
    const r = await fetch("/api/reports/all");
    const arr = await r.json();
    const list = document.getElementById("allReportsList");
    list.innerHTML = "";
    if (arr.length === 0) { list.innerHTML = "<div class='muted'>No reports yet.</div>"; }
    arr.forEach(item => {
      const d = document.createElement("div");
      d.className = "report-card";
      d.innerHTML = `<strong>${item.category}</strong> — ${item.location}<div style="margin-top:6px">${item.description}</div>
        <div style="margin-top:6px"><small>User: ${item.user}</small></div>
        <div style="margin-top:6px"><small>AI: ${item.ai_response ?? "—"}</small></div>
        <div style="margin-top:6px"><small>Tx: ${item.tx_hash ? item.tx_hash.substring(0,12) + "..." : "pending"}</small></div>`;
      list.appendChild(d);
    });
    document.getElementById("allModal").classList.add("open");
  } catch(e) {
    console.error("Open all reports error", e);
    Toastify({ text: "Could not fetch reports.", duration: 4000 }).showToast();
  }
}

// Socket setup
function setupSocket() {
  socket.on("connect", () => console.log("socket connected"));
  socket.on("new_report", (data) => {
    Toastify({ text: `New report: ${data.category} — ${data.location}`, duration: 5000 }).showToast();
    loadStats();
    // if the user is viewing All Reports, refresh it
    if (document.getElementById("allModal").classList.contains("open")) openAllReports();
  });
}
