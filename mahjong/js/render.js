// Canvas 渲染 — 程式繪製牌面,無需圖檔
// 座標系:玩家 0 在下方,1 右,2 上,3 左

const TILE_W = 38;
const TILE_H = 52;
const TILE_RADIUS = 4;
const HAND_GAP = 2;

function drawTile(ctx, x, y, tile, opts = {}) {
  const { facedown = false, rotation = 0, highlight = false, dimmed = false } = opts;
  ctx.save();
  ctx.translate(x + TILE_W / 2, y + TILE_H / 2);
  ctx.rotate(rotation);
  ctx.translate(-TILE_W / 2, -TILE_H / 2);

  // 牌身底色
  const grad = ctx.createLinearGradient(0, 0, 0, TILE_H);
  if (facedown) {
    grad.addColorStop(0, '#1a6b3f');
    grad.addColorStop(1, '#0d4426');
  } else {
    grad.addColorStop(0, '#fefdf6');
    grad.addColorStop(1, '#ddd5b8');
  }
  ctx.fillStyle = grad;
  roundRect(ctx, 0, 0, TILE_W, TILE_H, TILE_RADIUS);
  ctx.fill();

  // 邊框
  ctx.strokeStyle = facedown ? '#063318' : '#8a7d52';
  ctx.lineWidth = 1.5;
  ctx.stroke();

  if (highlight) {
    ctx.strokeStyle = '#ffcc00';
    ctx.lineWidth = 2;
    roundRect(ctx, -1, -1, TILE_W + 2, TILE_H + 2, TILE_RADIUS);
    ctx.stroke();
  }

  if (!facedown) {
    drawTileFace(ctx, tile);
  } else {
    // 牌背紋路
    ctx.fillStyle = 'rgba(255,255,255,0.1)';
    ctx.beginPath();
    ctx.arc(TILE_W / 2, TILE_H / 2, 8, 0, Math.PI * 2);
    ctx.fill();
  }

  if (dimmed) {
    ctx.fillStyle = 'rgba(0,0,0,0.35)';
    ctx.fillRect(0, 0, TILE_W, TILE_H);
  }
  ctx.restore();
}

function drawTileFace(ctx, tile) {
  if (!tile) return;
  const isRed = (tile.suit === 'z' && tile.num === 5) ||
                (tile.suit === 'm' && tile.num >= 1 && tile.num <= 9 && tile.num === 5) ||
                tile.isFlower();
  const color = isRed ? '#c01818' : (tile.suit === 's' ? '#0a7b2c' : '#222');

  ctx.fillStyle = color;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  if (tile.suit === 'z') {
    // 字牌:中央放大字
    ctx.font = 'bold 22px "Noto Sans TC", "Microsoft YaHei", serif';
    const ch = ['', '東','南','西','北','中','發','白'][tile.num];
    ctx.fillText(ch, TILE_W / 2, TILE_H / 2 + 1);
  } else if (tile.suit === 'f') {
    ctx.font = 'bold 20px "Noto Sans TC", serif';
    const ch = ['', '春','夏','秋','冬','梅','蘭','竹','菊'][tile.num];
    ctx.fillStyle = tile.num <= 4 ? '#c01818' : '#0a7b2c';
    ctx.fillText(ch, TILE_W / 2, TILE_H / 2 + 1);
  } else {
    // 數牌:上方數字,下方花色
    ctx.font = 'bold 18px "Microsoft YaHei", serif';
    const numCh = ['', '一','二','三','四','五','六','七','八','九'][tile.num];
    ctx.fillText(numCh, TILE_W / 2, TILE_H / 2 - 9);

    ctx.font = 'bold 14px "Microsoft YaHei", serif';
    const suitCh = { m: '萬', p: '筒', s: '索' }[tile.suit];
    ctx.fillText(suitCh, TILE_W / 2, TILE_H / 2 + 12);
  }
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

class Renderer {
  constructor(canvas, game) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.game = game;
    this.handHitboxes = []; // [{x,y,w,h,tileIdx}]
    this.discardClickable = null;
    this.claimButtons = [];
  }

  setGame(g) { this.game = g; }

  draw() {
    const ctx = this.ctx;
    const W = this.canvas.width;
    const H = this.canvas.height;
    // 桌布
    const bg = ctx.createRadialGradient(W/2, H/2, 50, W/2, H/2, Math.max(W, H));
    bg.addColorStop(0, '#1a7048');
    bg.addColorStop(1, '#093520');
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, W, H);

    // 中央資訊
    this.drawCenter();

    // 四個玩家
    this.handHitboxes = [];
    this.drawPlayerSouth(0);
    this.drawPlayerEast(1);
    this.drawPlayerNorth(2);
    this.drawPlayerWest(3);

    // 棄牌堆
    this.drawDiscards();

    // log
    this.drawLog();
  }

  drawCenter() {
    const ctx = this.ctx;
    const W = this.canvas.width, H = this.canvas.height;
    const cx = W / 2, cy = H / 2;
    ctx.fillStyle = 'rgba(0,0,0,0.25)';
    roundRect(ctx, cx - 100, cy - 60, 200, 120, 8);
    ctx.fill();

    ctx.fillStyle = '#fff';
    ctx.font = 'bold 14px sans-serif';
    ctx.textAlign = 'center';
    const windCh = ['', '東','南','西','北'][this.game.roundWind];
    ctx.fillText(`${windCh}圈`, cx, cy - 35);
    ctx.font = '12px sans-serif';
    ctx.fillText(`剩餘 ${this.game.wall.length} 張`, cx, cy - 12);
    ctx.fillText(`莊家:${this.game.players[this.game.dealerIdx].name}`, cx, cy + 8);
    if (this.game.lianzhuang > 0) ctx.fillText(`連${this.game.lianzhuang}拉${this.game.lianzhuang}`, cx, cy + 28);
    // 目前回合指示
    const cur = this.game.currentIdx;
    ctx.fillStyle = '#ffcc00';
    ctx.font = 'bold 12px sans-serif';
    ctx.fillText(`輪到:${this.game.players[cur].name}`, cx, cy + 48);
  }

  drawPlayerSouth(idx) {
    const ctx = this.ctx;
    const W = this.canvas.width, H = this.canvas.height;
    const p = this.game.players[idx];
    const hand = p.hand;
    const totalW = hand.length * (TILE_W + HAND_GAP);
    let x = (W - totalW) / 2;
    const y = H - TILE_H - 20;

    for (let i = 0; i < hand.length; i++) {
      const isLast = p.justDrew && i === hand.length - 1;
      const drawX = isLast ? x + 10 : x;
      drawTile(ctx, drawX, y, hand[i]);
      this.handHitboxes.push({ x: drawX, y, w: TILE_W, h: TILE_H, tileIdx: i, tileId: hand[i].id });
      x += TILE_W + HAND_GAP;
      if (isLast) x += 10;
    }
    // 副露
    let mx = W - 20;
    for (let m = p.melds.length - 1; m >= 0; m--) {
      const meld = p.melds[m];
      const tilesArr = meld.tiles.map(id => ({ suit: id[0], num: parseInt(id.slice(1), 10), display: () => id, isFlower: () => false, isHonor: () => id[0] === 'z' }));
      for (let t = tilesArr.length - 1; t >= 0; t--) {
        mx -= (TILE_W + 2);
        drawTile(ctx, mx, y - TILE_H - 8, tilesArr[t], { facedown: meld.type === 'ankan' && t !== 0 && t !== tilesArr.length - 1 });
      }
      mx -= 6;
    }
    // 花牌
    this.drawFlowers(p.flowers, 20, y - TILE_H - 8);
    // 玩家名
    ctx.fillStyle = idx === this.game.currentIdx ? '#ffcc00' : '#fff';
    ctx.font = 'bold 14px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(`${p.name} (${['','東','南','西','北'][p.seatWind]})  分:${p.score}`, 20, H - 5);
  }

  drawPlayerEast(idx) {
    const ctx = this.ctx;
    const W = this.canvas.width, H = this.canvas.height;
    const p = this.game.players[idx];
    const hand = p.hand;
    const x = W - TILE_H - 20;
    const totalH = hand.length * (TILE_W + HAND_GAP);
    let y = (H - totalH) / 2;
    for (let i = 0; i < hand.length; i++) {
      drawTile(ctx, x, y, hand[i], { facedown: true, rotation: -Math.PI / 2 });
      y += TILE_W + HAND_GAP;
    }
    // 副露
    let my = 20;
    for (const meld of p.melds) {
      for (const id of meld.tiles) {
        const t = { suit: id[0], num: parseInt(id.slice(1), 10) };
        drawTile(ctx, x - TILE_H - 8, my, t, { rotation: -Math.PI / 2 });
        my += TILE_W + 2;
      }
      my += 6;
    }
    this.drawFlowers(p.flowers, x - TILE_H - 8, H - 100, true);
    ctx.save();
    ctx.translate(W - 12, H / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillStyle = idx === this.game.currentIdx ? '#ffcc00' : '#fff';
    ctx.font = 'bold 14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(`${p.name} (${['','東','南','西','北'][p.seatWind]})  ${p.score}`, 0, 0);
    ctx.restore();
  }

  drawPlayerNorth(idx) {
    const ctx = this.ctx;
    const W = this.canvas.width;
    const p = this.game.players[idx];
    const hand = p.hand;
    const totalW = hand.length * (TILE_W + HAND_GAP);
    let x = (W - totalW) / 2;
    const y = 20;
    for (let i = 0; i < hand.length; i++) {
      drawTile(ctx, x, y, hand[i], { facedown: true, rotation: Math.PI });
      x += TILE_W + HAND_GAP;
    }
    let mx = 20;
    for (const meld of p.melds) {
      for (const id of meld.tiles) {
        const t = { suit: id[0], num: parseInt(id.slice(1), 10) };
        drawTile(ctx, mx, y + TILE_H + 8, t, { rotation: Math.PI });
        mx += TILE_W + 2;
      }
      mx += 6;
    }
    this.drawFlowers(p.flowers, W - 200, y + TILE_H + 8);
    ctx.fillStyle = idx === this.game.currentIdx ? '#ffcc00' : '#fff';
    ctx.font = 'bold 14px sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(`${p.name} (${['','東','南','西','北'][p.seatWind]})  ${p.score}`, W - 20, 15);
  }

  drawPlayerWest(idx) {
    const ctx = this.ctx;
    const H = this.canvas.height;
    const p = this.game.players[idx];
    const hand = p.hand;
    const x = 20;
    const totalH = hand.length * (TILE_W + HAND_GAP);
    let y = (H - totalH) / 2;
    for (let i = 0; i < hand.length; i++) {
      drawTile(ctx, x, y, hand[i], { facedown: true, rotation: Math.PI / 2 });
      y += TILE_W + HAND_GAP;
    }
    let my = H - 100;
    for (const meld of p.melds) {
      for (const id of meld.tiles) {
        const t = { suit: id[0], num: parseInt(id.slice(1), 10) };
        drawTile(ctx, x + TILE_H + 8, my, t, { rotation: Math.PI / 2 });
        my -= TILE_W + 2;
      }
      my -= 6;
    }
    this.drawFlowers(p.flowers, x + TILE_H + 8, 20);
    ctx.save();
    ctx.translate(12, H / 2);
    ctx.rotate(Math.PI / 2);
    ctx.fillStyle = idx === this.game.currentIdx ? '#ffcc00' : '#fff';
    ctx.font = 'bold 14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(`${p.name} (${['','東','南','西','北'][p.seatWind]})  ${p.score}`, 0, 0);
    ctx.restore();
  }

  drawFlowers(flowers, x, y, vertical = false) {
    const ctx = this.ctx;
    const small = 24;
    for (let i = 0; i < flowers.length; i++) {
      const fx = vertical ? x : x + i * (small + 2);
      const fy = vertical ? y + i * (small + 2) : y;
      ctx.fillStyle = '#fef8e0';
      roundRect(ctx, fx, fy, small, small, 3);
      ctx.fill();
      ctx.strokeStyle = '#8a7d52';
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.fillStyle = flowers[i].num <= 4 ? '#c01818' : '#0a7b2c';
      ctx.font = 'bold 14px "Noto Sans TC", serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      const ch = ['', '春','夏','秋','冬','梅','蘭','竹','菊'][flowers[i].num];
      ctx.fillText(ch, fx + small/2, fy + small/2 + 1);
    }
  }

  drawDiscards() {
    const ctx = this.ctx;
    const W = this.canvas.width, H = this.canvas.height;
    const cx = W / 2, cy = H / 2;
    // 各家棄牌位置
    const positions = [
      { startX: cx - 100, startY: cy + 70, dx: TILE_W * 0.7, dy: 0, rot: 0 },
      { startX: cx + 70, startY: cy - 100, dx: 0, dy: TILE_W * 0.7, rot: -Math.PI/2 },
      { startX: cx + 100, startY: cy - 70, dx: -TILE_W * 0.7, dy: 0, rot: Math.PI },
      { startX: cx - 70, startY: cy + 100, dx: 0, dy: -TILE_W * 0.7, rot: Math.PI/2 }
    ];
    for (let p = 0; p < 4; p++) {
      const pos = positions[p];
      const discards = this.game.players[p].discards;
      for (let i = 0; i < discards.length; i++) {
        const row = Math.floor(i / 6);
        const col = i % 6;
        let dx = pos.dx * col;
        let dy = pos.dy * col;
        // 自然換行邏輯(各方向不同)
        if (p === 0 || p === 2) dy += (p === 0 ? row * TILE_H : -row * TILE_H);
        else dx += (p === 1 ? row * TILE_H : -row * TILE_H);
        drawTile(ctx, pos.startX + dx, pos.startY + dy, discards[i], { rotation: pos.rot });
      }
    }
  }

  drawLog() {
    const ctx = this.ctx;
    ctx.fillStyle = 'rgba(0,0,0,0.45)';
    roundRect(ctx, 8, 38, 220, 110, 6);
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    const lines = this.game.log.slice(-8);
    for (let i = 0; i < lines.length; i++) {
      ctx.fillText(lines[i], 14, 44 + i * 13);
    }
  }
}

if (typeof module !== 'undefined') {
  module.exports = { Renderer, drawTile, TILE_W, TILE_H };
}
