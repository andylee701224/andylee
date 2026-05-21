// 胡牌判定:台灣 16 張 = 5 面子 + 1 對子
// 面子 = 順子(同花色連 3 張,字牌不能順) 或 刻子(3 同) 或 槓子(4 同,佔 1 面子)
// 輸入:手牌 tiles (不含花牌、不含已副露的牌) + 既有副露數 meldsCount + 多 1 張的「胡牌」
// 設計:遞迴拆解。先取對子,剩下分組為面子。

// 將手牌轉為「花色 -> 9 格陣列」便於演算
function toCountArrays(tiles) {
  const arr = { m: new Array(10).fill(0), p: new Array(10).fill(0), s: new Array(10).fill(0), z: new Array(8).fill(0) };
  for (const t of tiles) {
    if (t.suit === 'f') continue;
    arr[t.suit][t.num]++;
  }
  return arr;
}

// 嘗試把單一花色拆成 needMelds 個面子 (順+刻)。回傳 true 表成功。
function canFormMelds(counts, needMelds, allowSequence) {
  if (needMelds === 0) {
    for (let i = 1; i < counts.length; i++) if (counts[i] !== 0) return false;
    return true;
  }
  // 找第一個非零位置
  let i = 1;
  while (i < counts.length && counts[i] === 0) i++;
  if (i >= counts.length) return false;

  // 嘗試刻子
  if (counts[i] >= 3) {
    counts[i] -= 3;
    if (canFormMelds(counts, needMelds - 1, allowSequence)) { counts[i] += 3; return true; }
    counts[i] += 3;
  }
  // 嘗試順子
  if (allowSequence && i + 2 < counts.length && counts[i] >= 1 && counts[i+1] >= 1 && counts[i+2] >= 1) {
    counts[i]--; counts[i+1]--; counts[i+2]--;
    if (canFormMelds(counts, needMelds - 1, allowSequence)) {
      counts[i]++; counts[i+1]++; counts[i+2]++;
      return true;
    }
    counts[i]++; counts[i+1]++; counts[i+2]++;
  }
  return false;
}

// 判定剩餘手牌 + 1 張胡牌是否能組成 (existingMelds + needTotalMelds) 面子 + 1 對
// hand: 不含花牌的所有牌 (含手上的 + 摸入或榮和的那張)
// existingMelds: 已副露面子數 (含明槓暗槓)
function canWin(hand, existingMelds) {
  // 16 張 + 1 = 17 張結構,需 5 面子 + 1 對,扣除已副露
  const totalMelds = 5;
  const needMelds = totalMelds - existingMelds;
  if (needMelds < 0) return false;
  const expectedTileCount = needMelds * 3 + 2;
  if (hand.length !== expectedTileCount) return false;

  const c = toCountArrays(hand);
  // 嘗試每一張作為對子
  const allSuits = ['m', 'p', 's', 'z'];
  for (const suit of allSuits) {
    const arr = c[suit];
    const maxN = suit === 'z' ? 7 : 9;
    for (let n = 1; n <= maxN; n++) {
      if (arr[n] >= 2) {
        arr[n] -= 2;
        // 拆解每個花色為若干面子
        if (tryAllSuits(c, needMelds)) {
          arr[n] += 2;
          return true;
        }
        arr[n] += 2;
      }
    }
  }
  return false;
}

// 把四個花色拆成總計 needMelds 個面子
function tryAllSuits(c, needMelds) {
  // 先算每個花色剩餘牌數
  // 字牌只能刻子;m/p/s 可順可刻
  // 因為單一花色面子數不能跨花色拼,所以分別嘗試
  return helper(c, ['m', 'p', 's', 'z'], 0, needMelds);
}

function helper(c, suits, idx, remain) {
  if (idx === suits.length) return remain === 0;
  const suit = suits[idx];
  const arr = c[suit];
  const total = arr.reduce((s, x) => s + x, 0);
  if (total === 0) return helper(c, suits, idx + 1, remain);
  if (total % 3 !== 0) return false;
  const needHere = total / 3;
  if (needHere > remain) return false;
  // 拆解此花色
  if (!canFormMelds(arr, needHere, suit !== 'z')) return false;
  return helper(c, suits, idx + 1, remain - needHere);
}

// 找出聽牌:返回所有可使本手牌胡的「下一張牌 id」
function findWaitingTiles(hand, existingMelds) {
  const result = [];
  const trySet = new Set();
  for (const suit of ['m','p','s']) for (let n = 1; n <= 9; n++) trySet.add(`${suit}${n}`);
  for (let n = 1; n <= 7; n++) trySet.add(`z${n}`);
  for (const id of trySet) {
    const t = { suit: id[0], num: parseInt(id.slice(1), 10) };
    const cnt = hand.filter(x => x.suit === t.suit && x.num === t.num).length;
    if (cnt >= 4) continue;
    const trial = hand.concat([t]);
    if (canWin(trial, existingMelds)) result.push(id);
  }
  return result;
}

// 列舉所有可能的「組合分解」(用於台型判定 — 平胡需要全順子等)
// 回傳:Array<{ pair: tileId, melds: Array<{type:'chi'|'pon', tiles:[id,id,id]}> }>
function enumerateWinPatterns(hand, existingMelds) {
  const patterns = [];
  const totalMelds = 5;
  const needMelds = totalMelds - existingMelds;
  const c = toCountArrays(hand);

  for (const suit of ['m','p','s','z']) {
    const arr = c[suit];
    const maxN = suit === 'z' ? 7 : 9;
    for (let n = 1; n <= maxN; n++) {
      if (arr[n] >= 2) {
        arr[n] -= 2;
        const acc = [];
        decomposeAll(c, ['m','p','s','z'], 0, needMelds, acc, patterns, `${suit}${n}`);
        arr[n] += 2;
      }
    }
  }
  return patterns;
}

function decomposeAll(c, suits, idx, remain, acc, results, pairId) {
  if (idx === suits.length) {
    if (remain === 0) results.push({ pair: pairId, melds: acc.slice() });
    return;
  }
  const suit = suits[idx];
  const arr = c[suit];
  const total = arr.reduce((s, x) => s + x, 0);
  if (total === 0) { decomposeAll(c, suits, idx + 1, remain, acc, results, pairId); return; }
  if (total % 3 !== 0) return;
  const needHere = total / 3;
  if (needHere > remain) return;
  // 在此花色內列舉所有面子拆法
  decomposeSuit(arr, suit, needHere, acc, () => {
    decomposeAll(c, suits, idx + 1, remain - needHere, acc, results, pairId);
  });
}

function decomposeSuit(arr, suit, needMelds, acc, cont) {
  if (needMelds === 0) { cont(); return; }
  let i = 1;
  while (i < arr.length && arr[i] === 0) i++;
  if (i >= arr.length) return;
  // 刻子
  if (arr[i] >= 3) {
    arr[i] -= 3;
    acc.push({ type: 'pon', tiles: [`${suit}${i}`, `${suit}${i}`, `${suit}${i}`] });
    decomposeSuit(arr, suit, needMelds - 1, acc, cont);
    acc.pop();
    arr[i] += 3;
  }
  // 順子 (僅 m/p/s)
  if (suit !== 'z' && i + 2 < arr.length && arr[i] >= 1 && arr[i+1] >= 1 && arr[i+2] >= 1) {
    arr[i]--; arr[i+1]--; arr[i+2]--;
    acc.push({ type: 'chi', tiles: [`${suit}${i}`, `${suit}${i+1}`, `${suit}${i+2}`] });
    decomposeSuit(arr, suit, needMelds - 1, acc, cont);
    acc.pop();
    arr[i]++; arr[i+1]++; arr[i+2]++;
  }
}

if (typeof module !== 'undefined') {
  module.exports = { canWin, findWaitingTiles, enumerateWinPatterns };
}
