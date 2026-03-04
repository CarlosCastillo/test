const canvas = document.getElementById('world');
const ctx = canvas.getContext('2d');

const antCountEl = document.getElementById('antCount');
const foodCountEl = document.getElementById('foodCount');
const scoreEl = document.getElementById('score');

const spawnFoodBtn = document.getElementById('spawnFood');
const toggleBtn = document.getElementById('toggle');
const resetBtn = document.getElementById('reset');

let width = 0;
let height = 0;
let paused = false;
let delivered = 0;

const nest = { x: 0, y: 0, r: 18 };
let ants = [];
let foods = [];

function resize() {
  width = canvas.clientWidth;
  height = canvas.clientHeight;
  canvas.width = width;
  canvas.height = height;
  nest.x = width * 0.5;
  nest.y = height * 0.5;
}

function rand(min, max) {
  return Math.random() * (max - min) + min;
}

function createAnt() {
  return {
    x: nest.x + rand(-10, 10),
    y: nest.y + rand(-10, 10),
    angle: rand(0, Math.PI * 2),
    speed: rand(0.8, 1.5),
    carrying: false,
  };
}

function spawnFood(amount = 30) {
  for (let i = 0; i < amount; i += 1) {
    foods.push({ x: rand(30, width - 30), y: rand(30, height - 30), r: 4 });
  }
}

function resetWorld() {
  ants = Array.from({ length: 60 }, createAnt);
  foods = [];
  delivered = 0;
  spawnFood(60);
  updateStats();
}

function updateStats() {
  antCountEl.textContent = String(ants.length);
  foodCountEl.textContent = String(foods.length);
  scoreEl.textContent = String(delivered);
}

function nearestFood(ant) {
  let best = null;
  let bestDist = Infinity;

  for (let i = 0; i < foods.length; i += 1) {
    const f = foods[i];
    const dx = f.x - ant.x;
    const dy = f.y - ant.y;
    const d2 = dx * dx + dy * dy;
    if (d2 < bestDist) {
      bestDist = d2;
      best = { food: f, idx: i, dist: Math.sqrt(d2), dx, dy };
    }
  }
  return best;
}

function stepAnt(ant) {
  if (!ant.carrying) {
    const target = nearestFood(ant);
    if (target && target.dist < 120) {
      ant.angle = Math.atan2(target.dy, target.dx);
      if (target.dist < 6) {
        foods.splice(target.idx, 1);
        ant.carrying = true;
      }
    } else {
      ant.angle += rand(-0.2, 0.2);
    }
  } else {
    const dx = nest.x - ant.x;
    const dy = nest.y - ant.y;
    const dist = Math.hypot(dx, dy);
    ant.angle = Math.atan2(dy, dx);
    if (dist < nest.r + 2) {
      ant.carrying = false;
      delivered += 1;
    }
  }

  ant.x += Math.cos(ant.angle) * ant.speed;
  ant.y += Math.sin(ant.angle) * ant.speed;

  if (ant.x < 0 || ant.x > width) {
    ant.angle = Math.PI - ant.angle;
    ant.x = Math.max(0, Math.min(width, ant.x));
  }
  if (ant.y < 0 || ant.y > height) {
    ant.angle = -ant.angle;
    ant.y = Math.max(0, Math.min(height, ant.y));
  }
}

function drawWorld() {
  ctx.fillStyle = '#0b1220';
  ctx.fillRect(0, 0, width, height);

  ctx.beginPath();
  ctx.arc(nest.x, nest.y, nest.r, 0, Math.PI * 2);
  ctx.fillStyle = '#f59e0b';
  ctx.fill();

  for (const food of foods) {
    ctx.beginPath();
    ctx.arc(food.x, food.y, food.r, 0, Math.PI * 2);
    ctx.fillStyle = '#22c55e';
    ctx.fill();
  }

  for (const ant of ants) {
    ctx.beginPath();
    ctx.arc(ant.x, ant.y, 2.2, 0, Math.PI * 2);
    ctx.fillStyle = ant.carrying ? '#f8fafc' : '#ef4444';
    ctx.fill();
  }
}

function tick() {
  if (!paused) {
    for (const ant of ants) stepAnt(ant);
    updateStats();
  }
  drawWorld();
  requestAnimationFrame(tick);
}

spawnFoodBtn.addEventListener('click', () => {
  spawnFood(30);
  updateStats();
});

toggleBtn.addEventListener('click', () => {
  paused = !paused;
  toggleBtn.textContent = paused ? 'Reanudar' : 'Pausar';
});

resetBtn.addEventListener('click', resetWorld);

window.addEventListener('resize', resize);

resize();
resetWorld();
tick();
