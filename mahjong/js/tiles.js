// 台灣麻將牌定義
// suit: 'm'=萬, 'p'=筒, 's'=索, 'z'=字, 'f'=花
// num : 1-9 (m/p/s), 1-7 (z: 東南西北中發白), 1-8 (f: 春夏秋冬梅蘭竹菊)

const SUITS = { MAN: 'm', PIN: 'p', SOU: 's', HONOR: 'z', FLOWER: 'f' };

const HONOR_NAMES = ['', '東', '南', '西', '北', '中', '發', '白'];
const FLOWER_NAMES = ['', '春', '夏', '秋', '冬', '梅', '蘭', '竹', '菊'];

// Unicode 牌面 (用於文字顯示備援)
const UNICODE_TILES = {
  m: ['', '🀇','🀈','🀉','🀊','🀋','🀌','🀍','🀎','🀏'],
  p: ['', '🀙','🀚','🀛','🀜','🀝','🀞','🀟','🀠','🀡'],
  s: ['', '🀐','🀑','🀒','🀓','🀔','🀕','🀖','🀗','🀘'],
  z: ['', '🀀','🀁','🀂','🀃','🀄','🀅','🀆'],
  f: ['', '🀢','🀣','🀤','🀥','🀦','🀧','🀨','🀩']
};

class Tile {
  constructor(suit, num) {
    this.suit = suit;
    this.num = num;
    this.id = `${suit}${num}`;
  }
  // 用於排序/比較的整數鍵
  key() {
    const order = { m: 0, p: 1, s: 2, z: 3, f: 4 };
    return order[this.suit] * 10 + this.num;
  }
  equals(t) { return t && this.suit === t.suit && this.num === t.num; }
  isHonor() { return this.suit === 'z'; }
  isFlower() { return this.suit === 'f'; }
  isTerminal() {
    return (this.suit !== 'z' && this.suit !== 'f') && (this.num === 1 || this.num === 9);
  }
  isWind() { return this.suit === 'z' && this.num >= 1 && this.num <= 4; }
  isDragon() { return this.suit === 'z' && this.num >= 5 && this.num <= 7; }
  // 顯示文字 (備援,Canvas 會自己畫)
  display() {
    if (this.suit === 'z') return HONOR_NAMES[this.num];
    if (this.suit === 'f') return FLOWER_NAMES[this.num];
    const suitChar = { m: '萬', p: '筒', s: '索' }[this.suit];
    return `${this.num}${suitChar}`;
  }
  unicode() { return UNICODE_TILES[this.suit][this.num]; }
  clone() { return new Tile(this.suit, this.num); }
}

// 建立完整 144 張牌
function buildFullDeck() {
  const tiles = [];
  for (const suit of ['m', 'p', 's']) {
    for (let n = 1; n <= 9; n++) {
      for (let i = 0; i < 4; i++) tiles.push(new Tile(suit, n));
    }
  }
  // 字牌 7 種 × 4
  for (let n = 1; n <= 7; n++) {
    for (let i = 0; i < 4; i++) tiles.push(new Tile('z', n));
  }
  // 花牌 8 種 × 1
  for (let n = 1; n <= 8; n++) tiles.push(new Tile('f', n));
  return tiles;
}

function sortTiles(tiles) {
  return tiles.slice().sort((a, b) => a.key() - b.key());
}

// 從 id 字串恢復 Tile
function tileFromId(id) {
  return new Tile(id[0], parseInt(id.slice(1), 10));
}

// 將手牌轉為 {id: count} 計數
function tilesToCount(tiles) {
  const c = {};
  for (const t of tiles) c[t.id] = (c[t.id] || 0) + 1;
  return c;
}

if (typeof module !== 'undefined') {
  module.exports = { Tile, SUITS, HONOR_NAMES, FLOWER_NAMES, buildFullDeck, sortTiles, tileFromId, tilesToCount, UNICODE_TILES };
}
