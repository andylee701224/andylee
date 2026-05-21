// 規則式 AI:
//   1) 永遠優先胡(若可胡)
//   2) 評估每張手牌的「打掉成本」,挑成本最低者
//   3) 吃/碰/槓:評估能否讓聽牌數量增加或形成關鍵刻子;字牌(中發白、本家風)優先碰
// 評估方法:shanten 距離簡化版 — 「打掉後距離胡牌張數」近似為手牌結構性破壞程度

const { canWin, findWaitingTiles } = (typeof require !== 'undefined') ? require('./win.js') : window;

// 計算手牌中每張牌「孤立度」分數(高=容易打掉)
function isolationScore(tile, hand) {
  if (tile.isHonor()) {
    const sameCount = hand.filter(t => t.id === tile.id).length;
    if (sameCount === 1) return 10; // 單張字牌極易丟
    if (sameCount === 2) return 3;
    return 0;
  }
  // 數牌:看左右是否有相鄰
  let s = 0;
  const n = tile.num;
  const neighbors = hand.filter(t => t.suit === tile.suit && Math.abs(t.num - n) <= 2 && t.id !== tile.id);
  if (neighbors.length === 0) s += 8;
  if (neighbors.length <= 1) s += 3;
  if (n === 1 || n === 9) s += 1;
  const sameCount = hand.filter(t => t.id === tile.id).length;
  if (sameCount >= 2) s -= 5; // 對子/刻子保留
  if (sameCount >= 3) s -= 8;
  return s;
}

// 決定要打哪張牌
function chooseDiscard(player) {
  const hand = player.hand;
  // 1) 若可胡(自摸)
  if (canWin(hand, player.melds.length)) {
    return { winSelf: true };
  }
  // 2) 評估每張的孤立度
  let bestIdx = 0;
  let bestScore = -Infinity;
  for (let i = 0; i < hand.length; i++) {
    const s = isolationScore(hand[i], hand);
    if (s > bestScore) { bestScore = s; bestIdx = i; }
  }
  return { tileId: hand[bestIdx].id };
}

// 決定是否吃 / 碰 / 槓 / 胡 別人棄牌
// 回傳:{ action: 'win'|'pon'|'kan'|'chi'|'pass', tiles? }
function chooseClaim(player, discard, fromIdx, canChi) {
  // 1) 若可胡(榮和)
  const trial = player.hand.concat([discard]);
  if (canWin(trial, player.melds.length)) {
    return { action: 'win' };
  }
  // 2) 槓:手中 3 張同牌
  const sameCount = player.hand.filter(t => t.id === discard.id).length;
  if (sameCount >= 3) {
    return { action: 'kan' };
  }
  // 3) 碰:手中 2 張同牌
  if (sameCount >= 2) {
    // 字牌(尤其三元/本家風)強烈傾向碰;數牌看孤立度
    if (discard.isHonor()) {
      const n = discard.num;
      if (n >= 5 || n === player.seatWind || n === 1) return { action: 'pon' }; // 三元或門風或東(圈風候選)
      return { action: 'pon' };
    }
    // 數牌:若是中張(3-7)較傾向碰
    if (discard.num >= 3 && discard.num <= 7) return { action: 'pon' };
    return { action: 'pon' };
  }
  // 4) 吃(只有下家可以吃)
  if (canChi && !discard.isHonor()) {
    const opts = enumerateChiOptions(player.hand, discard);
    if (opts.length > 0) {
      // 取破壞最小的吃法 — 簡化:取第一個
      return { action: 'chi', tiles: opts[0] };
    }
  }
  return { action: 'pass' };
}

// 列舉吃的選項:回傳手牌中可組成順子的 2 張 id 陣列
function enumerateChiOptions(hand, discard) {
  if (discard.isHonor() || discard.isFlower()) return [];
  const suit = discard.suit;
  const n = discard.num;
  const has = (k) => hand.find(t => t.suit === suit && t.num === k);
  const opts = [];
  // n-2, n-1, n
  if (n >= 3 && has(n-2) && has(n-1)) opts.push([`${suit}${n-2}`, `${suit}${n-1}`]);
  // n-1, n, n+1
  if (n >= 2 && n <= 8 && has(n-1) && has(n+1)) opts.push([`${suit}${n-1}`, `${suit}${n+1}`]);
  // n, n+1, n+2
  if (n <= 7 && has(n+1) && has(n+2)) opts.push([`${suit}${n+1}`, `${suit}${n+2}`]);
  return opts;
}

// 暗槓決策:手中 4 張同牌且暗槓不會破壞胡型 — 簡化:有就槓
function maybeAnGang(player) {
  const counts = {};
  for (const t of player.hand) counts[t.id] = (counts[t.id] || 0) + 1;
  for (const id of Object.keys(counts)) if (counts[id] === 4) return id;
  return null;
}

if (typeof module !== 'undefined') {
  module.exports = { chooseDiscard, chooseClaim, enumerateChiOptions, maybeAnGang };
}
