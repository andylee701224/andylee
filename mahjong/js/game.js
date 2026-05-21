// 遊戲流程主控
// 玩家編號:0=東(下方/玩家),1=南(右),2=西(上),3=北(左)
// 風位以「莊家所在玩家編號」對應「東」,順時針南西北

const PHASES = {
  WAITING_DRAW: 'WAITING_DRAW',     // 等待目前玩家摸牌
  WAITING_DISCARD: 'WAITING_DISCARD', // 摸完等待打牌
  WAITING_CLAIM: 'WAITING_CLAIM',   // 等待其他玩家宣告吃碰槓胡
  ENDED: 'ENDED'
};

class Player {
  constructor(idx, name, isAI) {
    this.idx = idx;
    this.name = name;
    this.isAI = isAI;
    this.hand = [];        // 手牌 (Tile[])
    this.melds = [];       // 副露 [{type, tiles, from}]
    this.flowers = [];     // 花牌 (Tile[])
    this.discards = [];    // 棄牌堆
    this.score = 0;
    this.seatWind = 1;     // 1=東 2=南 3=西 4=北
    this.justDrew = false; // 是否剛摸牌(用於暗槓/胡判定)
    this.menqing = true;   // 門清(無外露副露)
  }
}

class Game {
  constructor(playerNames) {
    this.players = playerNames.map((n, i) => new Player(i, n, i !== 0));
    this.dealerIdx = 0;
    this.roundWind = 1;
    this.lianzhuang = 0;   // 連莊次數
    this.totalRounds = 0;
    this.wall = [];        // 牌山
    this.deadWall = [];    // 王牌區(補花/槓尾)
    this.currentIdx = 0;
    this.phase = PHASES.WAITING_DRAW;
    this.lastDiscard = null;
    this.lastDiscardFrom = -1;
    this.pendingClaims = []; // 等待解決的宣告
    this.log = [];
    this.firstRound = true;  // 第一巡 (用於天胡/地胡)
    this.justGanged = false; // 用於槓上開花
  }

  pushLog(msg) { this.log.push(msg); if (this.log.length > 200) this.log.shift(); }

  startHand() {
    // 重置玩家
    for (const p of this.players) {
      p.hand = []; p.melds = []; p.flowers = []; p.discards = [];
      p.justDrew = false; p.menqing = true;
    }
    // 設定風位:莊家=東,順時針
    for (let i = 0; i < 4; i++) {
      const offset = (i - this.dealerIdx + 4) % 4;
      this.players[i].seatWind = ((offset) % 4) + 1; // 莊家=1(東)
    }
    // 洗牌
    this.wall = shuffle(buildFullDeck());
    this.firstRound = true;
    this.justGanged = false;
    // 發牌:莊家 17,其他 16
    for (let i = 0; i < 16; i++) {
      for (let p = 0; p < 4; p++) {
        this.players[(this.dealerIdx + p) % 4].hand.push(this.wall.pop());
      }
    }
    this.players[this.dealerIdx].hand.push(this.wall.pop()); // 莊家多一張
    // 補花(從牌尾):依序檢查每個玩家,把花牌拿出來放 flowers,再從牌尾摸補,直到無花
    this.replenishFlowers();
    // 排序手牌
    for (const p of this.players) p.hand = sortTiles(p.hand);
    this.currentIdx = this.dealerIdx;
    this.phase = PHASES.WAITING_DISCARD; // 莊家已有 17 張,直接打
    this.pushLog(`新局開始,莊家:${this.players[this.dealerIdx].name}`);
  }

  replenishFlowers() {
    let changed = true;
    while (changed) {
      changed = false;
      // 從莊家依序檢查
      for (let i = 0; i < 4; i++) {
        const p = this.players[(this.dealerIdx + i) % 4];
        for (let j = p.hand.length - 1; j >= 0; j--) {
          if (p.hand[j].isFlower()) {
            p.flowers.push(p.hand[j]);
            p.hand.splice(j, 1);
            if (this.wall.length > 0) p.hand.push(this.wall.shift()); // 從牌尾摸補(這裡用 shift 模擬 dead wall)
            changed = true;
          }
        }
      }
    }
  }

  // 玩家摸牌
  drawTile(playerIdx) {
    if (this.wall.length === 0) return null;
    const t = this.wall.pop();
    const p = this.players[playerIdx];
    let buhua = false;
    while (t && t.isFlower()) {
      p.flowers.push(t);
      buhua = true;
      if (this.wall.length === 0) break;
      const nxt = this.wall.shift(); // 從牌尾補
      if (!nxt) break;
      if (nxt.isFlower()) { p.flowers.push(nxt); continue; }
      p.hand.push(nxt);
      p.justDrew = true;
      this.phase = PHASES.WAITING_DISCARD;
      return { tile: nxt, buhua };
    }
    if (t && !t.isFlower()) {
      p.hand.push(t);
      p.justDrew = true;
      this.phase = PHASES.WAITING_DISCARD;
      return { tile: t, buhua };
    }
    return null;
  }

  // 棄牌
  discardTile(playerIdx, tileId) {
    const p = this.players[playerIdx];
    const idx = p.hand.findIndex(t => t.id === tileId);
    if (idx === -1) return false;
    const t = p.hand.splice(idx, 1)[0];
    p.discards.push(t);
    p.justDrew = false;
    this.lastDiscard = t;
    this.lastDiscardFrom = playerIdx;
    this.justGanged = false;
    this.phase = PHASES.WAITING_CLAIM;
    this.pushLog(`${p.name} 打出 ${t.display()}`);
    return true;
  }

  // 進到下一個玩家
  advanceTurn() {
    this.currentIdx = (this.currentIdx + 1) % 4;
    this.phase = PHASES.WAITING_DRAW;
    if (this.currentIdx === this.dealerIdx) this.firstRound = false;
  }

  // 副露:吃
  doChi(playerIdx, useTileIds) {
    // useTileIds:玩家手中的 2 張 + 別人棄牌 (lastDiscard)
    const p = this.players[playerIdx];
    const taken = [];
    for (const id of useTileIds) {
      const i = p.hand.findIndex(t => t.id === id);
      if (i === -1) return false;
      taken.push(p.hand.splice(i, 1)[0]);
    }
    const meldTiles = [...taken.map(t => t.id), this.lastDiscard.id].sort();
    p.melds.push({ type: 'chi', tiles: meldTiles, from: this.lastDiscardFrom });
    p.menqing = false;
    this.lastDiscard = null;
    this.currentIdx = playerIdx;
    this.phase = PHASES.WAITING_DISCARD;
    this.pushLog(`${p.name} 吃 ${meldTiles.join(',')}`);
    return true;
  }

  // 副露:碰
  doPon(playerIdx) {
    const p = this.players[playerIdx];
    const target = this.lastDiscard;
    const matches = p.hand.filter(t => t.id === target.id);
    if (matches.length < 2) return false;
    for (let i = 0; i < 2; i++) {
      const idx = p.hand.findIndex(t => t.id === target.id);
      p.hand.splice(idx, 1);
    }
    p.melds.push({ type: 'pon', tiles: [target.id, target.id, target.id], from: this.lastDiscardFrom });
    p.menqing = false;
    this.lastDiscard = null;
    this.currentIdx = playerIdx;
    this.phase = PHASES.WAITING_DISCARD;
    this.pushLog(`${p.name} 碰 ${target.display()}`);
    return true;
  }

  // 副露:槓(明槓 - 用別人棄牌)
  doMingGang(playerIdx) {
    const p = this.players[playerIdx];
    const target = this.lastDiscard;
    const matches = p.hand.filter(t => t.id === target.id);
    if (matches.length < 3) return false;
    for (let i = 0; i < 3; i++) {
      const idx = p.hand.findIndex(t => t.id === target.id);
      p.hand.splice(idx, 1);
    }
    p.melds.push({ type: 'kan', tiles: [target.id, target.id, target.id, target.id], from: this.lastDiscardFrom });
    p.menqing = false;
    this.lastDiscard = null;
    this.currentIdx = playerIdx;
    this.justGanged = true;
    // 槓完從牌尾摸 1 張(嶺上)
    const next = this.drawTile(playerIdx);
    this.pushLog(`${p.name} 槓 ${target.display()}`);
    return true;
  }

  // 暗槓:自己手中 4 張
  doAnGang(playerIdx, tileId) {
    const p = this.players[playerIdx];
    const matches = p.hand.filter(t => t.id === tileId);
    if (matches.length < 4) return false;
    for (let i = 0; i < 4; i++) {
      const idx = p.hand.findIndex(t => t.id === tileId);
      p.hand.splice(idx, 1);
    }
    p.melds.push({ type: 'ankan', tiles: [tileId, tileId, tileId, tileId], from: playerIdx });
    // 暗槓不破門清
    this.justGanged = true;
    this.pushLog(`${p.name} 暗槓 ${tileId}`);
    // 嶺上摸牌
    this.drawTile(playerIdx);
    return true;
  }

  // 結算胡牌:winnerIdx 胡了 tile (來自 fromIdx,若為 -1 表自摸)
  doWin(winnerIdx, winTile, fromIdx) {
    const p = this.players[winnerIdx];
    const isTsumo = fromIdx === -1 || fromIdx === winnerIdx;
    // 將胡牌加入手牌做計算
    const handForCalc = p.hand.slice();
    if (!isTsumo) handForCalc.push(winTile);
    const isDealer = winnerIdx === this.dealerIdx;
    const ctx = {
      hand: handForCalc,
      melds: p.melds,
      flowers: p.flowers,
      winTile,
      isTsumo,
      isDealer,
      roundWind: this.roundWind,
      seatWind: p.seatWind,
      isMenqing: p.menqing && p.melds.every(m => m.type === 'ankan'),
      isGangFlower: this.justGanged && isTsumo,
      isHaidi: this.wall.length === 0,
      isHeavenly: isDealer && this.firstRound && p.discards.length === 0 && isTsumo,
      isEarthly: !isDealer && this.firstRound && p.discards.length === 0,
      lianzhuang: this.lianzhuang
    };
    const result = bestTai(ctx);
    this.phase = PHASES.ENDED;
    this.lastWin = { winnerIdx, fromIdx, tile: winTile, ...result };
    // 連莊判定
    if (winnerIdx === this.dealerIdx) this.lianzhuang++;
    else { this.lianzhuang = 0; this.dealerIdx = (this.dealerIdx + 1) % 4; }
    this.pushLog(`${p.name} 胡牌!共 ${result.total} 台`);
    return result;
  }

  // 流局
  drawnGame() {
    this.phase = PHASES.ENDED;
    this.lastWin = { winnerIdx: -1, total: 0, tais: [] };
    this.pushLog('流局');
  }
}

function shuffle(arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

if (typeof module !== 'undefined') {
  module.exports = { Game, Player, PHASES };
}
