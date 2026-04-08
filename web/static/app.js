const BOARD_SIZE = 15;
const EMPTY = " ";
const BLACK = "X";
const WHITE = "O";

const sideSelect = document.getElementById("sideSelect");
const newBtn = document.getElementById("newBtn");
const statusEl = document.getElementById("status");
const boardEl = document.getElementById("board");
const intersectionsEl = document.getElementById("intersections");

let grid = [];
let toMove = BLACK;
let gameOver = false;
let winner = null;
let isDraw = false;
let lastMove = null;

function emptyGrid() {
  const g = [];
  for (let r = 0; r < BOARD_SIZE; r++) {
    const row = [];
    for (let c = 0; c < BOARD_SIZE; c++) row.push(EMPTY);
    g.push(row);
  }
  return g;
}

function cloneGrid(g) {
  return g.map((row) => row.slice());
}

function setStatus(text) {
  statusEl.textContent = text;
}

function humanSideStone() {
  return sideSelect.value === "white" ? WHITE : BLACK;
}

function deriveLastMove(prev, next, humanCoord) {
  const added = [];
  for (let r = 0; r < BOARD_SIZE; r++) {
    for (let c = 0; c < BOARD_SIZE; c++) {
      const p = prev?.[r]?.[c] ?? EMPTY;
      if (p === EMPTY && next[r][c] !== EMPTY) added.push([r, c]);
    }
  }
  if (added.length === 0) return null;
  if (added.length === 1) return { r: added[0][0], c: added[0][1] };
  if (humanCoord) {
    const [hr, hc] = humanCoord;
    const other = added.find(([r, c]) => r !== hr || c !== hc);
    if (other) return { r: other[0], c: other[1] };
  }
  const last = added[added.length - 1];
  return { r: last[0], c: last[1] };
}


function intersectionPositionStyle(r, c) {
  return {
    left: `calc(var(--pad) + ${c} * var(--gap))`,
    top: `calc(var(--pad) + ${r} * var(--gap))`,
  };
}

function renderBoard() {
  intersectionsEl.innerHTML = "";

  for (let r = 0; r < BOARD_SIZE; r++) {
    for (let c = 0; c < BOARD_SIZE; c++) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "intersection";
      btn.dataset.row = String(r);
      btn.dataset.col = String(c);
      const pos = intersectionPositionStyle(r, c);
      btn.style.left = pos.left;
      btn.style.top = pos.top;

      const preview = document.createElement("span");
      preview.className = "stone preview";
      if (humanSideStone() === BLACK) preview.classList.add("black");
      else preview.classList.add("white");
      preview.setAttribute("aria-hidden", "true");

      const stone = document.createElement("span");
      stone.className = "stone";
      stone.setAttribute("aria-hidden", "true");

      const v = grid[r][c];
      if (v === BLACK) {
        stone.classList.add("black", "is-visible");
      } else if (v === WHITE) {
        stone.classList.add("white", "is-visible");
      }

      const lastDot = document.createElement("span");
      lastDot.className = "last-dot";
      lastDot.setAttribute("aria-hidden", "true");

      if (lastMove && lastMove.r === r && lastMove.c === c && v !== EMPTY) {
        btn.classList.add("is-last");
      }

      const canClick = !gameOver && toMove === humanSideStone() && v === EMPTY;
      btn.disabled = !canClick;

      btn.appendChild(preview);
      btn.appendChild(stone);
      btn.appendChild(lastDot);

      btn.addEventListener("click", () => handleCellClick(r, c));

      intersectionsEl.appendChild(btn);
    }
  }
}

function setBoardWaiting(waiting) {
  boardEl.classList.toggle("board--waiting", waiting);
}

function updateStatusLine() {
  if (gameOver) {
    if (winner === BLACK) setStatus("Black wins.");
    else if (winner === WHITE) setStatus("White wins.");
    else if (isDraw) setStatus("Draw.");
    else setStatus("Game over.");
    return;
  }
  const side = toMove === BLACK ? "Black" : "White";
  const yours = toMove === humanSideStone();
  setStatus(yours ? `Your turn (${side}).` : `AI thinking (${side} to move)…`);
}

function applyServerState(data, opts = {}) {
  const prev = opts.prevGrid ?? null;
  const humanCoord = opts.humanMove ?? null;

  grid = data.grid;
  toMove = data.to_move;
  gameOver = !!data.game_over;
  winner = data.winner ?? null;
  isDraw = !!data.is_draw;

  lastMove = deriveLastMove(prev, data.grid, humanCoord);
  renderBoard();
  updateStatusLine();
}

async function apiNew() {
  setStatus("Starting…");
  gameOver = true;
  lastMove = null;
  renderBoard();

  const side = sideSelect.value;
  const res = await fetch(`/api/new?side=${encodeURIComponent(side)}`);
  const data = await res.json();
  if (!res.ok) {
    setStatus(data.error || "Failed to start game.");
    grid = emptyGrid();
    gameOver = true;
    lastMove = null;
    renderBoard();
    return;
  }
  applyServerState(data, { prevGrid: emptyGrid() });
}

async function handleCellClick(row, col) {
  const r = row;
  const c = col;
  if (gameOver || toMove !== humanSideStone()) return;
  if (grid[r][c] !== EMPTY) return;

  const prevGrid = cloneGrid(grid);

  setStatus("Sending move…");
  setBoardWaiting(true);

  const res = await fetch("/api/move", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      grid,
      human_side: sideSelect.value,
      to_move: toMove,
      move: [r, c],
    }),
  });
  const data = await res.json();
  setBoardWaiting(false);

  if (!res.ok) {
    setStatus(data.error || "Move failed.");
    renderBoard();
    updateStatusLine();
    return;
  }
  applyServerState(data, { prevGrid, humanMove: [r, c] });
}

newBtn.addEventListener("click", () => {
  apiNew();
});

grid = emptyGrid();
gameOver = true;
lastMove = null;
renderBoard();
setStatus('Click "New Game" to play.');
