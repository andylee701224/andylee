// 簡易 Node 測試:確認牌堆、胡牌判定、台數計算正常
const { Tile, buildFullDeck, sortTiles, tileFromId } = require('../js/tiles.js');
const { canWin, findWaitingTiles, enumerateWinPatterns } = require('../js/win.js');
const { calculateTai, bestTai } = require('../js/tai.js');

let passed = 0, failed = 0;
function assert(cond, name) {
  if (cond) { passed++; console.log(`✓ ${name}`); }
  else { failed++; console.log(`✗ ${name}`); }
}

// 1) 牌堆正確
const deck = buildFullDeck();
assert(deck.length === 144, '牌堆總共 144 張');
const flowers = deck.filter(t => t.suit === 'f');
assert(flowers.length === 8, '花牌 8 張');
const m9 = deck.filter(t => t.suit === 'm' && t.num === 9);
assert(m9.length === 4, '9 萬 4 張');

// 2) 胡牌判定 - 簡單平胡
// 萬:123, 456, 789  筒:123, 456  索:11 (對子)  字:中中中
function H(...ids) { return ids.map(tileFromId); }
const hand1 = H('m1','m2','m3','m4','m5','m6','m7','m8','m9','p1','p2','p3','p4','p5','p6','s1','s1');
assert(canWin(hand1, 0) === true, '17 張全順子 + 對子可胡');

// 3) 不可胡
const hand2 = H('m1','m2','m3','m4','m5','m6','m7','m8','m9','p1','p2','p3','p4','p5','p6','s1','s2');
assert(canWin(hand2, 0) === false, '末尾 s1+s2 不能形成對子');

// 4) 碰碰胡:5 個刻子 + 1 對
const hand3 = H('m1','m1','m1','m5','m5','m5','p2','p2','p2','p9','p9','p9','s4','s4','s4','z5','z5');
assert(canWin(hand3, 0) === true, '碰碰胡可胡');

// 5) 副露 + 手牌
// 已副露 2 組 (假設),手牌 = 11 張 + 摸 = 11 應為 3 面子 + 1 對 = 11 張
const hand4 = H('m1','m2','m3','p4','p5','p6','s7','s8','s9','z1','z1');
assert(canWin(hand4, 2) === true, '副露 2 組 + 11 張可胡');

// 6) 聽牌計算
const tenpai = H('m1','m2','m3','m4','m5','m6','m7','m8','m9','p1','p2','p3','p4','p5','p6','s1');
const waits = findWaitingTiles(tenpai, 0);
assert(waits.includes('s1'), '聽 s1');

// 7) 台數計算 - 平胡
const ctx = {
  hand: hand1,
  melds: [],
  flowers: [],
  winTile: tileFromId('s1'),
  isTsumo: true,
  isDealer: false,
  roundWind: 1,
  seatWind: 2,
  isMenqing: true,
  pattern: null
};
const result = bestTai(ctx);
assert(result.total > 0, `平胡台數 > 0 (實得 ${result.total})`);
assert(result.tais.some(t => t.name.includes('平胡') || t.name.includes('門清')),
  `應有平胡或門清:${result.tais.map(t=>t.name).join(',')}`);

// 8) 大三元
const dasanyuan = H('z5','z5','z5','z6','z6','z6','z7','z7','z7','m1','m2','m3','p4','p5','p6','s1','s1');
const ctx2 = {
  hand: dasanyuan, melds: [], flowers: [],
  winTile: tileFromId('s1'), isTsumo: false, isDealer: false,
  roundWind: 1, seatWind: 2, isMenqing: true, pattern: null
};
const r2 = bestTai(ctx2);
assert(r2.total >= 8, `大三元 ≥ 8 台 (實得 ${r2.total})`);
assert(r2.tais.some(t => t.name === '大三元'), '應含大三元');

// 9) 清一色
const qingyise = H('m1','m1','m1','m2','m3','m4','m5','m6','m7','m7','m7','m8','m8','m8','m9','m9','m9');
// 上述是 17 張,需可拆 5 面子 + 1 對
const ctx3 = {
  hand: qingyise, melds: [], flowers: [],
  winTile: tileFromId('m9'), isTsumo: true, isDealer: false,
  roundWind: 1, seatWind: 2, isMenqing: true, pattern: null
};
const r3 = bestTai(ctx3);
console.log(`  清一色拆解:total=${r3.total}, 台型=${r3.tais.map(t=>t.name).join(',')}`);
assert(r3.tais.some(t => t.name === '清一色'), '應含清一色');

console.log(`\n結果:${passed} 通過,${failed} 失敗`);
process.exit(failed === 0 ? 0 : 1);
