// 台灣麻將台數計算 (神來也風格)
// 輸入:WinContext
//   hand: 不含花的所有牌(含胡牌),17 張
//   melds: 副露 [{type:'chi'|'pon'|'kan'|'ankan', tiles:[..]}]
//   flowers: 花牌陣列
//   winTile: 胡的那張 (tile)
//   isTsumo: 自摸
//   isDealer: 莊家
//   roundWind: 圈風 (1=東,2=南,3=西,4=北)
//   seatWind: 門風 (1=東 自己對應方位)
//   isMenqing: 門清 (無副露,暗槓允許)
//   isGangFlower: 槓上開花
//   isHaidi: 海底撈月
//   isQiangGang: 搶槓胡
//   isHeavenly: 天胡
//   isEarthly: 地胡
//   isBuhua: 補花胡 (摸到花補牌時直接胡)
//   pattern: 來自 enumerateWinPatterns 的分解 (含 pair + melds)
//   playerIdx: 玩家位置 (0=東,1=南,2=西,3=北)

const { enumerateWinPatterns } = (typeof require !== 'undefined') ? require('./win.js') : window;

// 正花對應:東=春/梅,南=夏/蘭,西=秋/竹,北=冬/菊
function isCorrectFlower(flowerNum, seatWind) {
  // flower 1-4=春夏秋冬(對應東南西北), 5-8=梅蘭竹菊(對應東南西北)
  const seasonMatch = flowerNum >= 1 && flowerNum <= 4 && flowerNum === seatWind;
  const plantMatch = flowerNum >= 5 && flowerNum <= 8 && (flowerNum - 4) === seatWind;
  return seasonMatch || plantMatch;
}

function calculateTai(ctx) {
  const tais = [];
  const add = (name, n) => { if (n > 0) tais.push({ name, tai: n }); };

  // === 基本台 ===
  if (ctx.isDealer) add('莊家', 1);
  if (ctx.lianzhuang && ctx.lianzhuang > 0) add(`連${ctx.lianzhuang}拉${ctx.lianzhuang}`, ctx.lianzhuang * 2);
  if (ctx.isTsumo) add('自摸', 1);
  if (ctx.isMenqing && !ctx.isTsumo) add('門清', 1);
  if (ctx.isMenqing && ctx.isTsumo) add('門清自摸', 3); // 取代門清+自摸,共 3 台
  // 上面若同時加了「自摸」「門清」「門清自摸」會重複,需處理:
  // 採規則:門清自摸 = 自摸(1) + 門清(1) + 門清自摸額外(1) = 3 台,但分開列;這裡簡化重整
  if (ctx.isMenqing && ctx.isTsumo) {
    // 移除剛剛加的「門清」「自摸」與「門清自摸」,重新加「門清自摸」3 台
    for (let i = tais.length - 1; i >= 0; i--) {
      if (['門清', '自摸', '門清自摸'].includes(tais[i].name)) tais.splice(i, 1);
    }
    tais.push({ name: '門清自摸', tai: 3 });
  }

  // === 花牌 ===
  const flowers = ctx.flowers || [];
  for (const f of flowers) {
    if (isCorrectFlower(f.num, ctx.seatWind)) add(`正花(${f.display()})`, 1);
    else add(`花牌(${f.display()})`, 1);
  }
  // 八仙過海 / 七搶一
  if (flowers.length >= 8) add('八仙過海', 8);

  // === 牌型台 ===
  const pattern = ctx.pattern; // { pair, melds: [{type:'chi'|'pon', tiles}] }
  const allMelds = [...(ctx.melds || []).map(normMeld), ...pattern.melds];
  const pairId = pattern.pair;

  // 平胡:全順子 + 對子不是字 + 胡牌位置非邊張坎張單騎 (簡化:全順子即可)
  const allChi = allMelds.every(m => m.type === 'chi');
  if (allChi && ctx.isMenqing) add('平胡', 2);

  // 碰碰胡:全刻子/槓子
  const allPon = allMelds.every(m => m.type === 'pon' || m.type === 'kan' || m.type === 'ankan');
  if (allPon) add('碰碰胡', 4);

  // 色相關
  const usedSuits = new Set();
  const allTileIds = [];
  for (const m of allMelds) for (const t of m.tiles) { usedSuits.add(t[0]); allTileIds.push(t); }
  allTileIds.push(pairId, pairId);
  usedSuits.add(pairId[0]);

  if (usedSuits.size === 1 && !usedSuits.has('z')) add('清一色', 8);
  else if (usedSuits.has('z') && (usedSuits.size === 2)) add('混一色', 4);
  else if (usedSuits.size === 1 && usedSuits.has('z')) add('字一色', 16);

  // 三元 / 四喜
  const honorPonIds = allMelds
    .filter(m => (m.type === 'pon' || m.type === 'kan' || m.type === 'ankan') && m.tiles[0][0] === 'z')
    .map(m => parseInt(m.tiles[0].slice(1), 10));
  const dragonPons = honorPonIds.filter(n => n >= 5).length;
  const windPons = honorPonIds.filter(n => n <= 4).length;
  const pairIsDragon = pairId[0] === 'z' && parseInt(pairId.slice(1), 10) >= 5;
  const pairIsWind = pairId[0] === 'z' && parseInt(pairId.slice(1), 10) <= 4;

  if (dragonPons === 3) add('大三元', 8);
  else if (dragonPons === 2 && pairIsDragon) add('小三元', 4);
  if (windPons === 4) add('大四喜', 16);
  else if (windPons === 3 && pairIsWind) add('小四喜', 8);

  // 三元牌單組 +1
  for (const n of honorPonIds.filter(x => x >= 5)) {
    if (dragonPons < 3) add(`三元(${['','','','','','中','發','白'][n]})`, 1);
  }
  // 圈風 / 門風 +1
  for (const n of honorPonIds.filter(x => x <= 4)) {
    if (n === ctx.roundWind) add('圈風', 1);
    if (n === ctx.seatWind) add('門風', 1);
  }

  // 槓子加台
  for (const m of allMelds) {
    if (m.type === 'kan') add('明槓', 1);
    if (m.type === 'ankan') add('暗槓', 2);
  }

  // === 特殊狀況 ===
  if (ctx.isHeavenly) add('天胡', 8);
  if (ctx.isEarthly) add('地胡', 8);
  if (ctx.isGangFlower) add('槓上開花', 1);
  if (ctx.isHaidi) add(ctx.isTsumo ? '海底撈月' : '海底撈魚', 1);
  if (ctx.isQiangGang) add('搶槓胡', 1);
  if (ctx.isBuhua) add('花胡', 1);

  // 獨聽(單騎/邊張/坎張)+1
  if (ctx.singleWait) add('獨聽', 1);

  const total = tais.reduce((s, x) => s + x.tai, 0);
  return { tais, total };
}

function normMeld(m) {
  // 確保 副露 meld 格式統一
  return { type: m.type, tiles: m.tiles };
}

// 嘗試所有 pattern,選擇台數最大的
function bestTai(ctx) {
  const patterns = enumerateWinPatterns(ctx.hand, (ctx.melds || []).length);
  if (patterns.length === 0) return { tais: [], total: 0, pattern: null };
  let best = null;
  for (const p of patterns) {
    const r = calculateTai({ ...ctx, pattern: p });
    if (!best || r.total > best.total) best = { ...r, pattern: p };
  }
  return best;
}

if (typeof module !== 'undefined') {
  module.exports = { calculateTai, bestTai, isCorrectFlower };
}
