// 入口:組裝遊戲流程
// 玩家 0 為人類(座位:下方),其他 3 個為 AI

let game, renderer;
let pendingHumanClaim = null; // { discardTile, fromIdx, canChi, canPon, canKan, canWin }
let aiBusy = false;

function init() {
  const canvas = document.getElementById('table');
  resizeCanvas(canvas);
  window.addEventListener('resize', () => { resizeCanvas(canvas); if (renderer) renderer.draw(); });

  game = new Game(['你', '小明', '阿華', '小美']);
  renderer = new Renderer(canvas, game);

  canvas.addEventListener('click', onCanvasClick);
  document.getElementById('btn-new').addEventListener('click', startNewHand);
  document.getElementById('btn-pass').addEventListener('click', () => resolveHumanClaim('pass'));
  document.getElementById('btn-pon').addEventListener('click', () => resolveHumanClaim('pon'));
  document.getElementById('btn-kan').addEventListener('click', () => resolveHumanClaim('kan'));
  document.getElementById('btn-chi').addEventListener('click', () => resolveHumanClaim('chi'));
  document.getElementById('btn-win').addEventListener('click', () => resolveHumanClaim('win'));
  document.getElementById('btn-angang').addEventListener('click', tryAnGang);
  document.getElementById('btn-tsumo').addEventListener('click', tryTsumo);

  startNewHand();
}

function resizeCanvas(canvas) {
  const w = Math.min(window.innerWidth - 20, 1100);
  const h = Math.min(window.innerHeight - 80, 760);
  canvas.width = w;
  canvas.height = h;
}

function startNewHand() {
  game.startHand();
  renderer.setGame(game);
  renderer.draw();
  updateButtons();
  // 莊家是 AI 的話,讓 AI 先打
  if (game.players[game.currentIdx].isAI) {
    setTimeout(aiTurn, 600);
  } else {
    showStatus(`你是莊家,請打牌`);
  }
}

function onCanvasClick(e) {
  if (game.phase === 'ENDED') return;
  const rect = e.target.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  // 只能在輪到人類且需要打牌時點擊手牌
  if (game.currentIdx !== 0 || game.phase !== 'WAITING_DISCARD') return;
  for (const hb of renderer.handHitboxes) {
    if (x >= hb.x && x <= hb.x + hb.w && y >= hb.y && y <= hb.y + hb.h) {
      humanDiscard(hb.tileId);
      return;
    }
  }
}

function humanDiscard(tileId) {
  game.discardTile(0, tileId);
  // 排序手牌
  game.players[0].hand = sortTiles(game.players[0].hand);
  renderer.draw();
  // 詢問其他玩家是否要宣告(吃碰槓胡)
  setTimeout(resolveClaims, 400);
}

// 處理棄牌後的宣告流程
function resolveClaims() {
  const discard = game.lastDiscard;
  if (!discard) { nextTurn(); return; }
  const fromIdx = game.lastDiscardFrom;

  // 1) 先檢查所有玩家可否胡(優先級最高)
  for (let off = 1; off <= 3; off++) {
    const i = (fromIdx + off) % 4;
    const p = game.players[i];
    const trial = p.hand.concat([discard]);
    if (canWin(trial, p.melds.length)) {
      if (p.isAI) {
        // AI 自動宣告胡
        endWithWin(i, discard, fromIdx);
        return;
      } else {
        // 等人類選擇
        pendingHumanClaim = { discard, fromIdx, options: ['win', 'pass'] };
        // 同時也可能可以碰/吃,加入選項
        addOtherClaimOptions(p, discard, fromIdx, pendingHumanClaim);
        showClaimUI(pendingHumanClaim);
        return;
      }
    }
  }

  // 2) 檢查碰 / 槓(任何位置)
  for (let off = 1; off <= 3; off++) {
    const i = (fromIdx + off) % 4;
    const p = game.players[i];
    const same = p.hand.filter(t => t.id === discard.id).length;
    if (same >= 2) {
      if (p.isAI) {
        const decision = chooseClaim(p, discard, fromIdx, (i === (fromIdx + 1) % 4));
        if (decision.action === 'pon' || decision.action === 'kan') {
          if (decision.action === 'kan' && same >= 3) game.doMingGang(i);
          else game.doPon(i);
          renderer.draw();
          if (p.isAI) setTimeout(aiTurn, 600);
          else showStatus('請打牌');
          return;
        }
      } else {
        // 人類:給選項
        pendingHumanClaim = { discard, fromIdx, options: ['pass'] };
        if (same >= 2) pendingHumanClaim.options.push('pon');
        if (same >= 3) pendingHumanClaim.options.push('kan');
        showClaimUI(pendingHumanClaim);
        return;
      }
    }
  }

  // 3) 吃(下家)
  const nextIdx = (fromIdx + 1) % 4;
  const nextP = game.players[nextIdx];
  const chiOpts = enumerateChiOptions(nextP.hand, discard);
  if (chiOpts.length > 0 && !discard.isHonor()) {
    if (nextP.isAI) {
      const decision = chooseClaim(nextP, discard, fromIdx, true);
      if (decision.action === 'chi') {
        game.doChi(nextIdx, decision.tiles);
        renderer.draw();
        setTimeout(aiTurn, 600);
        return;
      }
    } else {
      pendingHumanClaim = { discard, fromIdx, options: ['pass', 'chi'], chiOpts };
      showClaimUI(pendingHumanClaim);
      return;
    }
  }

  // 沒人宣告,進到下一家
  nextTurn();
}

function addOtherClaimOptions(p, discard, fromIdx, claim) {
  const same = p.hand.filter(t => t.id === discard.id).length;
  if (same >= 2) claim.options.push('pon');
  if (same >= 3) claim.options.push('kan');
  if ((p.idx === (fromIdx + 1) % 4) && !discard.isHonor()) {
    const opts = enumerateChiOptions(p.hand, discard);
    if (opts.length > 0) { claim.options.push('chi'); claim.chiOpts = opts; }
  }
}

function showClaimUI(claim) {
  const setVis = (id, on) => document.getElementById(id).style.display = on ? 'inline-block' : 'none';
  setVis('btn-pass', true);
  setVis('btn-pon', claim.options.includes('pon'));
  setVis('btn-kan', claim.options.includes('kan'));
  setVis('btn-chi', claim.options.includes('chi'));
  setVis('btn-win', claim.options.includes('win'));
  showStatus(`${game.players[claim.fromIdx].name} 打出 ${claim.discard.display()},請選擇:`);
}

function hideClaimUI() {
  for (const id of ['btn-pass','btn-pon','btn-kan','btn-chi','btn-win']) {
    document.getElementById(id).style.display = 'none';
  }
}

function resolveHumanClaim(action) {
  if (!pendingHumanClaim) return;
  const { discard, fromIdx } = pendingHumanClaim;
  hideClaimUI();
  if (action === 'win') {
    endWithWin(0, discard, fromIdx);
    pendingHumanClaim = null;
    return;
  }
  if (action === 'pon') {
    game.doPon(0);
    pendingHumanClaim = null;
    renderer.draw();
    game.players[0].hand = sortTiles(game.players[0].hand);
    showStatus('請打牌');
    return;
  }
  if (action === 'kan') {
    game.doMingGang(0);
    game.players[0].hand = sortTiles(game.players[0].hand);
    pendingHumanClaim = null;
    renderer.draw();
    showStatus('請打牌(嶺上)');
    return;
  }
  if (action === 'chi') {
    // 選第一個吃法(簡化;TODO:讓人選擇)
    const opts = pendingHumanClaim.chiOpts;
    game.doChi(0, opts[0]);
    game.players[0].hand = sortTiles(game.players[0].hand);
    pendingHumanClaim = null;
    renderer.draw();
    showStatus('請打牌');
    return;
  }
  // pass
  pendingHumanClaim = null;
  // 繼續處理其他可能的宣告(略過此玩家)— 簡化:直接 nextTurn
  nextTurn();
}

function nextTurn() {
  game.lastDiscard = null;
  game.advanceTurn();
  // 結束條件:牌山空了
  if (game.wall.length === 0) {
    game.drawnGame();
    renderer.draw();
    showStatus('流局');
    return;
  }
  if (game.players[game.currentIdx].isAI) {
    setTimeout(aiTurn, 500);
  } else {
    // 人類摸牌
    const draw = game.drawTile(0);
    game.players[0].hand = sortTiles(game.players[0].hand);
    renderer.draw();
    updateButtons();
    if (canWin(game.players[0].hand, game.players[0].melds.length)) {
      showStatus('你可以自摸!或選擇打牌');
      document.getElementById('btn-tsumo').style.display = 'inline-block';
    } else {
      document.getElementById('btn-tsumo').style.display = 'none';
      showStatus('請打牌');
    }
    // 暗槓選項
    const ag = maybeAnGang(game.players[0]);
    document.getElementById('btn-angang').style.display = ag ? 'inline-block' : 'none';
  }
}

function aiTurn() {
  if (aiBusy) return;
  aiBusy = true;
  const i = game.currentIdx;
  const p = game.players[i];
  // 摸牌(若 phase 是 WAITING_DRAW)
  if (game.phase === 'WAITING_DRAW') {
    const r = game.drawTile(i);
    if (!r) { game.drawnGame(); renderer.draw(); aiBusy = false; showStatus('流局'); return; }
  }
  p.hand = sortTiles(p.hand);
  renderer.draw();
  // 思考延遲
  setTimeout(() => {
    const decision = chooseDiscard(p);
    if (decision.winSelf) {
      endWithWin(i, p.hand[p.hand.length - 1], -1);
      aiBusy = false;
      return;
    }
    game.discardTile(i, decision.tileId);
    p.hand = sortTiles(p.hand);
    renderer.draw();
    aiBusy = false;
    setTimeout(resolveClaims, 300);
  }, 500 + Math.random() * 500);
}

function tryAnGang() {
  const id = maybeAnGang(game.players[0]);
  if (!id) return;
  game.doAnGang(0, id);
  game.players[0].hand = sortTiles(game.players[0].hand);
  renderer.draw();
  document.getElementById('btn-angang').style.display = 'none';
  if (canWin(game.players[0].hand, game.players[0].melds.length)) {
    document.getElementById('btn-tsumo').style.display = 'inline-block';
  }
}

function tryTsumo() {
  endWithWin(0, game.players[0].hand[game.players[0].hand.length - 1], -1);
}

function endWithWin(winnerIdx, tile, fromIdx) {
  const result = game.doWin(winnerIdx, tile, fromIdx);
  renderer.draw();
  showWinModal(winnerIdx, result, fromIdx);
}

function showWinModal(winnerIdx, result, fromIdx) {
  const modal = document.getElementById('result-modal');
  const body = document.getElementById('result-body');
  const winner = game.players[winnerIdx];
  let html = `<h2>${winner.name} ${fromIdx === -1 || fromIdx === winnerIdx ? '自摸' : '胡牌'}!</h2>`;
  html += `<div class="tai-total">${result.total} 台</div>`;
  html += '<ul>';
  for (const t of result.tais) html += `<li>${t.name} <span>+${t.tai}</span></li>`;
  html += '</ul>';
  html += '<button onclick="document.getElementById(\'result-modal\').style.display=\'none\'; startNewHand();">下一局</button>';
  body.innerHTML = html;
  modal.style.display = 'flex';
  // 計分:贏家 +台數,輸家視情況均攤(這裡簡化:每台 10 分)
  const perTai = 10;
  if (fromIdx === -1 || fromIdx === winnerIdx) {
    // 自摸:三家各付 (total + 莊家加成)
    for (let i = 0; i < 4; i++) {
      if (i !== winnerIdx) {
        game.players[i].score -= result.total * perTai;
        winner.score += result.total * perTai;
      }
    }
  } else {
    // 放槍:放槍者付全部
    game.players[fromIdx].score -= result.total * perTai * 3;
    winner.score += result.total * perTai * 3;
  }
}

function updateButtons() {
  hideClaimUI();
  document.getElementById('btn-tsumo').style.display = 'none';
  document.getElementById('btn-angang').style.display = 'none';
}

function showStatus(msg) {
  document.getElementById('status').textContent = msg;
}

window.addEventListener('DOMContentLoaded', init);
